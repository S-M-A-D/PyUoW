# Units & Flow

A **Unit** is the atomic building block of PyUoW. A **Flow** is a chain of units composed with the `>>` operator.

Every unit is generic over two type variables:

- `CONTEXT` — the context type the unit operates on (a `BaseContext[Params]`).
- `OUT` — the final output type of the flow this unit belongs to.

## The unit hierarchy

```text
BaseUnit
   │
FlowUnit
   ├── ConditionalUnit  -- branches on a boolean
   ├── RunUnit          -- side-effects, falls through
   └── FinalUnit        -- terminates with a Result
         └── ErrorUnit  -- pre-loaded with an exception
```

All four are exported from `pyuow` (sync) and `pyuow.aio` (async). The sync and async surface is identical except for `async def`.

---

## ConditionalUnit

Branches on a boolean. Override `condition(...)` to return `True` (continue to the next unit) or `False` (call the `on_failure` unit).

```python
from pyuow import ConditionalUnit, ErrorUnit


class IsAuthenticated(ConditionalUnit[Ctx, Out]):
    def condition(self, ctx: Ctx) -> bool:
        return ctx.user is not None


flow = (
    IsAuthenticated(on_failure=ErrorUnit(exc=PermissionError("not signed in")))
    >> NextUnit()
    >> FinalUnit()
).build()
```

The `on_failure` slot is required at construction and must itself be a `FlowUnit` — typically an `ErrorUnit` or another terminal unit.

---

## RunUnit

Does side-effects and falls through to the next unit unconditionally. Override `run(...)` — it returns `None`.

```python
from pyuow import RunUnit


class SendEmail(RunUnit[Ctx, Out]):
    def __init__(self, *, mailer: Mailer) -> None:
        super().__init__()
        self._mailer = mailer

    def run(self, ctx: Ctx) -> None:
        self._mailer.send(ctx.params.email, "Welcome!")
```

If `run()` raises, the surrounding unit catches the exception and returns `Result.error(exc)` — subsequent units are skipped.

---

## FinalUnit

Terminates the flow. Override `finish(...)` to return the `Result`.

```python
from pyuow import FinalUnit, Result


class Success(FinalUnit[Ctx, OrderConfirmation]):
    def finish(self, ctx: Ctx) -> Result[OrderConfirmation]:
        return Result.ok(OrderConfirmation(id=ctx.order_id))
```

A FinalUnit must be the last unit in a flow. Chaining anything after it raises `FinalUnitError`.

---

## ErrorUnit

A pre-baked `FinalUnit` that always returns `Result.error(exc)`. Useful as `on_failure` for a `ConditionalUnit`.

```python
from pyuow import ErrorUnit


cond = MyCondition(on_failure=ErrorUnit(exc=ValueError("invalid input")))
```

---

## Composing with `>>`

The `__rshift__` operator chains units. The return value is the *right-hand* unit — chained calls work because every call returns the chained unit again. `.build()` returns the *root* of the chain ready to execute.

```python
flow = (
    StepA()
    >> StepB()
    >> StepC()
    >> Done()
).build()

result = flow(context)
```

### Build-time validation

`.build()` walks the chain and ensures it terminates in a `FinalUnit`. If a non-final unit has no successor, you get:

```python
from pyuow import FlowNotTerminatedError


bad_flow = StepA().build()
# raises FlowNotTerminatedError: StepA
```

This catches "I forgot to add the terminal step" before any context is ever passed in.

### Re-using units

A unit instance can be used in **only one chain**. Re-chaining the same instance into a second flow raises `CannotReassignUnitError`:

```python
shared = StepA()
flow_a = shared >> Done()         # OK
flow_b = OtherStep() >> shared    # raises CannotReassignUnitError
```

Create a fresh instance per flow.

---

## Async flow

Everything above has an async twin. Import from `pyuow.aio`:

```python
from pyuow.aio import (
    ConditionalUnit,
    ErrorUnit,
    FinalUnit,
    RunUnit,
)


class CheckStock(ConditionalUnit[Ctx, Out]):
    async def condition(self, ctx: Ctx) -> bool:
        return await inventory.has(ctx.params.sku)


class Reserve(RunUnit[Ctx, Out]):
    async def run(self, ctx: Ctx) -> None:
        await inventory.reserve(ctx.params.sku)


class Confirm(FinalUnit[Ctx, Out]):
    async def finish(self, ctx: Ctx) -> Result[Out]:
        return Result.ok(Out(...))


flow = (
    CheckStock(on_failure=ErrorUnit(exc=RuntimeError("no stock")))
    >> Reserve()
    >> Confirm()
).build()

result = await flow(context)
```

The operator chaining, `.build()` validation, and error semantics are identical to the sync version.

---

## Reference

- [`pyuow.unit`](../api/unit.md) — sync units
- [`pyuow.aio`](../api/aio.md) — async units
