# Context

A `Context` is the payload your flow operates on. It carries **params** (immutable inputs) plus any mutable or computed state the flow needs as it progresses.

## The two halves

### Params

`Params` are the inputs handed to the flow. They are frozen dataclasses extending `BaseParams`.

```python
from dataclasses import dataclass
from pyuow import BaseParams


@dataclass(frozen=True)
class OrderParams(BaseParams):
    customer_id: str
    sku: str
    quantity: int
```

### Context

`BaseContext[PARAMS]` is a Protocol with a single attribute: `params: PARAMS`. Any class with a `params` field that matches structurally satisfies it.

Two convenience bases are provided:

- **`BaseMutableContext`** — a mutable dataclass with one safety net: re-assigning an attribute that already exists raises `AttributeCannotBeOverriddenError`. Good for flows that compute and store intermediate state.
- **`BaseImmutableContext`** — a `frozen=True` dataclass. Good for pure pipelines.

```python
from dataclasses import dataclass
from pyuow import BaseContext, BaseMutableContext, BaseImmutableContext


@dataclass
class OrderContext(BaseContext[OrderParams]):
    params: OrderParams
    in_stock: bool = False


@dataclass
class MutableCtx(BaseMutableContext[OrderParams]):
    pricing: Pricing | None = None


@dataclass(frozen=True)
class ImmutableCtx(BaseImmutableContext[OrderParams]):
    fingerprint: str
```

## Mutable safety net

`BaseMutableContext` allows new attributes to be set but blocks overwrites:

```python
ctx = MutableCtx(params=OrderParams(...))
ctx.pricing = compute_pricing(ctx)   # OK - first assignment
ctx.pricing = something_else          # raises AttributeCannotBeOverriddenError
```

This catches an entire class of bugs where two units overwrite each other's contributions.

## Specialised contexts

PyUoW ships with two context flavours layered on top of `BaseContext`:

- **[`BaseDomainContext`](domain.md#batch-and-domain-context)** — adds a `Batch` field, used with `DomainTransactionalWorkManager` to flush domain changes after a flow runs.
- **[`InMemoryDataPointContext`](datapoints.md)** — a context with a built-in DataPoint producer/consumer registry. Pair it with `ProducesDataPoints` and `ConsumesDataPoints` units.

You can compose them — `BaseDomainContext` and `InMemoryDataPointContext` are designed to be mixed into your own context class.

## Reference

- [`pyuow.context`](../api/context.md) — `BaseContext`, `BaseParams`, mutable / immutable bases
