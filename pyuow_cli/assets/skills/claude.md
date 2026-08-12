---
name: pyuow
description: Use this skill whenever working with the PyUoW library (Unit of Work pattern for Python) — composable units, flows, Result, transactional work managers, and the SQLAlchemy adapter.
---

<!-- Generated for pyuow 0.11.0 -->

## When to use PyUoW

PyUoW is a Python implementation of the Unit of Work pattern. It gives you small, typed building blocks for business logic that compose into a flow and run inside a Work Manager that handles transactions, batching, and domain events.

Use it when you want business logic that reads top-to-bottom, separates orchestration from execution, and stays testable as it grows.

## Units

A Unit is the atomic building block. Every unit is generic over `CONTEXT` (a `BaseContext[Params]`) and `OUT` (the flow output type).

Hierarchy:

```
BaseUnit
   │
FlowUnit
   ├── ConditionalUnit  -- branches on a boolean
   ├── RunUnit          -- side-effects, falls through
   └── FinalUnit        -- terminates with a Result
         └── ErrorUnit   -- pre-loaded with an exception
```

- `ConditionalUnit` — override `condition(...)` to return `True` (continue) or `False` (call `on_failure`).
- `RunUnit` — override `run(...)` for side-effects; returns `None` and falls through.
- `FinalUnit` — override `finish(...)` to return `Result[OUT]`; must be last in the chain.
- `ErrorUnit` — a pre-baked `FinalUnit` that always returns `Result.error(exc)`.

All four are exported from `pyuow` (sync) and `pyuow.aio` (async). The sync and async surface is identical except for `async def`.

## Composing flows

Chain units with the `>>` operator, then call `.build()` to validate and return the root.

```python
flow = (
    StepA()
    >> StepB()
    >> StepC()
    >> Done()
).build()
```

`.build()` ensures the chain terminates in a `FinalUnit`. If it does not, you get `FinalUnitError`. A unit instance can only belong to one chain; re-chaining raises `CannotReassignUnitError`.

## Result

`Result` is the return envelope for every flow. It is a frozen dataclass with three states: `ok`, `error`, and `empty`.

```python
from pyuow import Result

ok    = Result.ok(42)
err   = Result.error(ValueError("nope"))
empty = Result.empty()
```

- `.get()` returns the value for ok, raises the wrapped exception for error, and raises `MissingOutError` for empty.
- `.raise_for_error()` validates without returning — use it in side-effect flows where you only care that the flow succeeded.
- `.unwrap_or(default)` returns the value for ok, otherwise the default. Never raises.
- `.map(fn)` applies a function to the ok value; error and empty pass through unchanged.
- `.and_then(fn)` binds a `Result`-returning operation; error and empty short-circuit.

## Context

A `Context` carries params (immutable inputs) plus any mutable or computed state.

`BaseContext[PARAMS]` is a Protocol with a single attribute: `params: PARAMS`. Two convenience bases are provided:

- `BaseMutableContext` — mutable dataclass that blocks re-assigning an existing attribute (`AttributeCannotBeOverriddenError`).
- `BaseImmutableContext` — frozen dataclass for pure pipelines.

Specialised flavours include `BaseDomainContext` (adds a `Batch` field) and `InMemoryDataPointContext` (producer/consumer registry). You can compose them — inherit from both to get domain batch handling + datapoint storage.

## DataPoints

DataPoints are typed contracts for what one unit produces and another consumes. They add explicit producer/consumer declarations to flows, catching missing data at runtime before it becomes a `KeyError` deep in business logic.

Core pieces:

- `BaseDataPointSpec[VALUE]` — a typed key with `name` and `ref_type`. Calling it creates a container: `spec(value)` returns `BaseDataPointContainer(spec, value)`.
- `InMemoryDataPointContext[PARAMS]` — a frozen `BaseContext` that doubles as a `BaseDataPointProducer` and `BaseDataPointConsumer`. Stores datapoints in a dict keyed by their spec.
- `ProducesDataPoints` — mixin for units that *write* datapoints. Declares `_produces: set[Spec]`. Use `self.to(producer).add(spec(value), ...)`.
- `ConsumesDataPoints` — mixin for units that *read* datapoints. Declares `_consumes: set[Spec]`. Use `self.out_of(consumer)[spec]`.

```python
from dataclasses import dataclass
from pyuow import BaseParams, RunUnit, FinalUnit, Result
from pyuow.context.datapoint.in_memory import InMemoryDataPointContext
from pyuow.datapoint import BaseDataPointSpec, ProducesDataPoints, ConsumesDataPoints


@dataclass(frozen=True)
class OrderParams(BaseParams):
    user_id: str


@dataclass(frozen=True)
class OrderCtx(InMemoryDataPointContext[OrderParams]):
    params: OrderParams


# Declare typed specs at module level
CartTotal = BaseDataPointSpec("cart_total", int)
TaxAmount = BaseDataPointSpec("tax_amount", int)


class ComputeCartTotal(RunUnit[OrderCtx, str], ProducesDataPoints):
    _produces = {CartTotal}

    def run(self, ctx: OrderCtx) -> None:
        total = 100  # lookup from service
        self.to(ctx).add(CartTotal(total))


class ApplyTax(RunUnit[OrderCtx, str], ConsumesDataPoints, ProducesDataPoints):
    _consumes = {CartTotal}
    _produces = {TaxAmount}

    def run(self, ctx: OrderCtx) -> None:
        total = self.out_of(ctx)[CartTotal]
        self.to(ctx).add(TaxAmount(total // 10))


class Summarise(FinalUnit[OrderCtx, str], ConsumesDataPoints):
    _consumes = {CartTotal, TaxAmount}

    def finish(self, ctx: OrderCtx) -> Result[str]:
        dp = self.out_of(ctx)
        return Result.ok(f"total={dp[CartTotal]} tax={dp[TaxAmount]}")
```

Enforcement at runtime:

| Mistake | Exception |
|---|---|
| Consumer requests a spec no producer wrote | `DataPointIsNotProducedError` |
| Producer writes a spec not declared in `_produces` | `DataPointIsNotDeclaredError` |
| Two producers write the same spec | `DataPointCannotBeOverriddenError` |
| Wrong value type passed to `spec(value)` | `TypeError` at call time |

### Combined context pattern

In real flows you often need **both** domain batch handling (for `DomainTransactionalWorkManager`) and datapoint storage. Compose the two context bases:

```python
from dataclasses import dataclass
from pyuow.context.domain import BaseDomainContext
from pyuow.context.datapoint.in_memory import InMemoryDataPointContext


@dataclass(frozen=True)
class OrderCtx(BaseDomainContext[OrderParams], InMemoryDataPointContext[OrderParams]):
    params: OrderParams
```

This gives you `ctx.batch` (for domain entity flushing) and `ctx.add()` / `ctx.get()` (for datapoints) in one context object. The unit mixins (`ProducesDataPoints`, `ConsumesDataPoints`) work unchanged — they only need a `BaseDataPointProducer` / `BaseDataPointConsumer`, which `InMemoryDataPointContext` provides.

Async twins: `pyuow.context.datapoint.aio.in_memory.InMemoryDataPointContext` and `pyuow.datapoint.aio.{ProducesDataPoints,ConsumesDataPoints}`. Method names are identical; only difference is `await` on `to(ctx).add(...)` and `out_of(ctx)`.

## Work Manager

A Work Manager runs a flow and wraps it with cross-cutting concerns. The pattern is:

```python
result = work.by(flow).do_with(context)
```

PyUoW ships four managers:

1. `NoOpWorkManager` — runs the flow with no extras. Good for tests.
2. `TransactionalWorkManager` — commits on success, rolls back on `Result.error(...)`.
3. `DomainTransactionalWorkManager` — transactional plus domain batch flushing and event dispatch.
4. Custom — subclass `BaseWorkManager` and `BaseUnitProxy`.

Async twins exist under `pyuow.work.aio.*`.

## Domain Model

`Model[ID]` (from `pyuow.domain`) is an event-emitting entity — it extends `AuditedEntity`, `SoftDeletableEntity`, and `VersionedEntity`. Subclasses implement `_generate_id()`, `_created_event()`, and `_deleted_event()`.

Three construction paths, three different meanings:

| Call | id | `is_new` | Created event |
|---|---|---|---|
| `Order(sku="WIDGET")` | generated by `_generate_id()` | `True` | yes |
| `Order.new(id=OrderId(...), sku="WIDGET")` | the one you passed | `True` | yes |
| `Order(id=OrderId(...), sku="WIDGET")` | the one you passed | `False` | no |

The plain constructor reads a supplied id as rehydration of an already-persisted entity: no creation event, and `Batch.add()` rejects it with `CannotAddExistingEntityError`. Use the `new()` classmethod when the id comes from outside — an upstream service, an idempotency key, a deterministic hash — but the entity itself is new:

```python
order = Order.new(id=OrderId(external_id), sku="WIDGET", quantity=3)

order.is_new          # True
order.events()        # (OrderCreated(model_id=external_id, ...),)
ctx.batch.add(order)  # accepted
```

Omit `id` and `new()` is equivalent to the plain constructor.

State changes stay immutable: `.update(event=..., **fields)` returns a copy with the event appended, `.delete()` sets `deleted_date` and appends a `ModelDeletedEvent`, and `.events()` returns the whole history as a tuple.

`Batch` collects those changes for `DomainTransactionalWorkManager` to flush — `add()` requires `is_new`, while `update()` and `delete()` require the opposite (`CannotUpdateNewEntityError` / `CannotDeleteNewEntityError`).

## Sync vs async

PyUoW is sync-first but provides an `aio/` twin for every module where async matters. Pure data modules (`pyuow.result`, `pyuow.context`, `pyuow.entity`, `pyuow.domain.base`) have no async version; use them unchanged in both sync and async code.

A flow cannot mix sync and async units. Pick one model per flow.

## SQLAlchemy

The integration lives under `pyuow.contrib.sqlalchemy` (sync) and `pyuow.contrib.sqlalchemy.aio` (async). It provides:

- `SqlAlchemyTransactionManager` / `SqlAlchemyReadOnlyTransactionManager` — for `TransactionalWorkManager`.
- `BaseSqlAlchemyEntityRepository` — implements `BaseEntityRepository` against `EntityTable` mixins.
- `BaseSqlAlchemyRepositoryFactory` — wires repositories for `DomainTransactionalWorkManager`.
- `BaseSqlAlchemyViewRepository` / `BaseSqlAlchemyViewRepositoryFactory` — read-only repositories over database views: implement `to_view`, then query with `select()` + `find_by` / `find_all_by` / `get_by` / `exists_by`.
- `EntityTable` / `AuditedEntityTable` / `SoftDeletableEntityTable` / `VersionedEntityTable` — `DeclarativeBase` mixins.
- `ViewTable` — `DeclarativeBase` mixin for a mapped database view; pair it with a plain frozen dataclass read model.

Install with `pip install "pyuow[sqlalchemy]"`.

## Common pitfalls

- Forgetting `.build()` — the chain is not callable until validated.
- Reusing a unit instance in two chains — raises `CannotReassignUnitError`.
- Chaining after a `FinalUnit` — raises `FinalUnitError`.
- Mixing sync and async units in one flow — signatures do not match.
- Overwriting a mutable context attribute — `BaseMutableContext` raises `AttributeCannotBeOverriddenError`.
- Building a brand-new `Model` as `Model(id=...)` — a supplied id means "already persisted" (`is_new=False`, no created event), so `Batch.add()` raises `CannotAddExistingEntityError`. Use `Model.new(id=...)`.

## Canonical example

```python
from dataclasses import dataclass

from pyuow import (
    BaseContext, BaseParams, ConditionalUnit, ErrorUnit,
    FinalUnit, Result, RunUnit,
)
from pyuow.work.noop import NoOpWorkManager


@dataclass(frozen=True)
class Greeting(BaseParams):
    name: str


@dataclass
class Ctx(BaseContext[Greeting]):
    params: Greeting


class IsNamePresent(ConditionalUnit[Ctx, str]):
    def condition(self, ctx: Ctx) -> bool:
        return bool(ctx.params.name)


class Greet(RunUnit[Ctx, str]):
    def run(self, ctx: Ctx) -> None:
        print(f"Hello, {ctx.params.name}!")


class Done(FinalUnit[Ctx, str]):
    def finish(self, ctx: Ctx) -> Result[str]:
        return Result.ok("greeted")


flow = (
    IsNamePresent(on_failure=ErrorUnit(exc=ValueError("name required")))
    >> Greet()
    >> Done()
).build()

result = NoOpWorkManager().by(flow).do_with(Ctx(params=Greeting(name="Alice")))
assert result.get() == "greeted"
```
