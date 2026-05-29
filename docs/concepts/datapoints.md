# DataPoints

DataPoints are a typed contract for **what one unit produces** and **what another consumes**. Instead of passing arbitrary values through the context, units declare their contributions and dependencies as typed specs, and the framework verifies them at runtime.

The pattern shines when a flow has several independent units that share data through the context — DataPoints catch missing/mismatched producers and consumers before they cause action-at-a-distance bugs.

---

## The shape

- **`BaseDataPointSpec[VALUE]`** — a typed key. Has a `name` and a `ref_type`. Calling the spec creates a typed container: `spec(value)` returns `BaseDataPointContainer(spec, value)`.
- **`BaseDataPointContainer[VALUE]`** — `(spec, value)` pair; what flows through the context's storage.
- **`ProducesDataPoints`** — mixin for units that *write* datapoints. Declares `_produces: set[Spec]`. Use `self.to(producer).add(spec(value), ...)`.
- **`ConsumesDataPoints`** — mixin for units that *read* datapoints. Declares `_consumes: set[Spec]`. Use `self.out_of(consumer)[spec]`.
- **`InMemoryDataPointContext`** — a `BaseContext` that doubles as producer + consumer; stores datapoints in a dict keyed by their spec.

---

## A complete example

```python
from dataclasses import dataclass

from pyuow import BaseParams, ConditionalUnit, ErrorUnit, FinalUnit, Result, RunUnit
from pyuow.context.datapoint.in_memory import InMemoryDataPointContext
from pyuow.datapoint import (
    BaseDataPointSpec,
    ConsumesDataPoints,
    ProducesDataPoints,
)


# 1. Define the params and context
@dataclass(frozen=True)
class CheckoutParams(BaseParams):
    user_id: str
    cart_id: str


@dataclass(frozen=True)
class CheckoutCtx(InMemoryDataPointContext[CheckoutParams]):
    params: CheckoutParams


# 2. Declare typed datapoint specs
CartTotal = BaseDataPointSpec("cart_total", int)
TaxAmount = BaseDataPointSpec("tax_amount", int)


# 3. A producer unit
class ComputeCartTotal(RunUnit[CheckoutCtx, str], ProducesDataPoints):
    _produces = {CartTotal}

    def run(self, ctx: CheckoutCtx) -> None:
        total = self._lookup(ctx.params.cart_id)
        self.to(ctx).add(CartTotal(total))


# 4. A consumer + producer unit
class ApplyTax(RunUnit[CheckoutCtx, str], ConsumesDataPoints, ProducesDataPoints):
    _consumes = {CartTotal}
    _produces = {TaxAmount}

    def run(self, ctx: CheckoutCtx) -> None:
        total = self.out_of(ctx)[CartTotal]
        self.to(ctx).add(TaxAmount(total // 10))


# 5. A consumer terminal
class Summarise(FinalUnit[CheckoutCtx, str], ConsumesDataPoints):
    _consumes = {CartTotal, TaxAmount}

    def finish(self, ctx: CheckoutCtx) -> Result[str]:
        dp = self.out_of(ctx)
        return Result.ok(f"total={dp[CartTotal]} tax={dp[TaxAmount]}")


# 6. Compose
flow = (
    ComputeCartTotal()
    >> ApplyTax()
    >> Summarise()
).build()
```

When the flow runs, the context's in-memory store collects datapoints as they're added. The framework checks at consume-time that every declared `_consumes` entry actually exists. If anything is missing, you get `DataPointIsNotProducedError` with the missing specs — never `KeyError` deep in business code.

---

## What gets enforced

| Mistake                                                | Exception                            |
| ------------------------------------------------------ | ------------------------------------ |
| A consumer requests a spec no producer wrote           | `DataPointIsNotProducedError`        |
| A producer writes a spec it did not declare in `_produces` | `DataPointIsNotDeclaredError`    |
| Two producers write the same spec to the same context  | `DataPointCannotBeOverriddenError`   |
| Wrong value type passed to a spec call                 | `TypeError` (at `spec(value)` time)  |

The first two errors come from the `ProducesDataPoints` / `ConsumesDataPoints` mixins. The third comes from `InMemoryDataPointContext` rejecting duplicates. The fourth is the spec itself — it `isinstance`-checks `value` against `ref_type`.

---

## Async variant

The async twins live under `pyuow.context.datapoint.aio.in_memory` and `pyuow.datapoint.aio`:

```python
from pyuow.aio import RunUnit
from pyuow.context.datapoint.aio.in_memory import InMemoryDataPointContext
from pyuow.datapoint.aio import ConsumesDataPoints, ProducesDataPoints


class ComputeCartTotal(RunUnit[CheckoutCtx, str], ProducesDataPoints):
    _produces = {CartTotal}

    async def run(self, ctx: CheckoutCtx) -> None:
        total = await self._lookup(ctx.params.cart_id)
        await self.to(ctx).add(CartTotal(total))


class Summarise(FinalUnit[CheckoutCtx, str], ConsumesDataPoints):
    _consumes = {CartTotal}

    async def finish(self, ctx: CheckoutCtx) -> Result[str]:
        dp = await self.out_of(ctx)
        return Result.ok(f"total={dp[CartTotal]}")
```

The sync and async producer/consumer mixins have identical method names; the only difference is `await`.

---

## When to use DataPoints

Use them when:

- A flow has 3+ units that share computed state.
- You want explicit contracts between units rather than ad-hoc context attributes.
- You catch missing/unused producer-consumer pairs at runtime before they cause incorrect behaviour deeper down.

Skip them when:

- The flow is short and the shared state is obvious from context attributes.
- The state is naturally tied to the params, not to intermediate computation.

---

## Reference

- [`pyuow.datapoint`](../api/datapoint.md)
- [`pyuow.context.datapoint`](../api/context.md)
