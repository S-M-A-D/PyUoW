# Quickstart

A small but complete PyUoW flow: a context, three units chained with `>>`, and a no-op Work Manager that runs them.

## 1. Define the params and context

`Params` are the inputs your flow needs. `Context` carries those params plus anything you want to compute as the flow progresses.

```python
from dataclasses import dataclass

from pyuow import BaseContext, BaseParams


@dataclass(frozen=True)
class OrderParams(BaseParams):
    customer_id: str
    sku: str
    quantity: int


@dataclass
class OrderContext(BaseContext[OrderParams]):
    params: OrderParams
    in_stock: bool = False
```

## 2. Write the units

A flow is built from units. The common four:

- [**ConditionalUnit**](concepts/units.md#conditionalunit) branches based on a boolean.
- [**RunUnit**](concepts/units.md#rununit) does side-effects and falls through to the next unit.
- [**FinalUnit**](concepts/units.md#finalunit) terminates the flow with a Result.
- [**ErrorUnit**](concepts/units.md#errorunit) is a FinalUnit pre-loaded with an exception.

```python
from pyuow import (
    ConditionalUnit,
    ErrorUnit,
    FinalUnit,
    Result,
    RunUnit,
)


@dataclass(frozen=True)
class OrderConfirmed:
    customer_id: str
    sku: str


class CheckStock(ConditionalUnit[OrderContext, OrderConfirmed]):
    def condition(self, ctx: OrderContext) -> bool:
        ctx.in_stock = ctx.params.quantity <= 5  # mocked
        return ctx.in_stock


class ReserveStock(RunUnit[OrderContext, OrderConfirmed]):
    def run(self, ctx: OrderContext) -> None:
        ...  # call an inventory service here


class Confirm(FinalUnit[OrderContext, OrderConfirmed]):
    def finish(self, ctx: OrderContext) -> Result[OrderConfirmed]:
        return Result.ok(
            OrderConfirmed(
                customer_id=ctx.params.customer_id, sku=ctx.params.sku
            )
        )
```

## 3. Compose the flow

`>>` chains units. `.build()` walks the chain and raises [`FlowNotTerminatedError`](concepts/units.md#build-time-validation) if a non-final unit has no successor.

```python
flow = (
    CheckStock(on_failure=ErrorUnit(exc=RuntimeError("out of stock")))
    >> ReserveStock()
    >> Confirm()
).build()
```

## 4. Run via a Work Manager

The simplest manager is `NoOpWorkManager`, which just runs the flow with no transaction wrapping. Production code usually wants the transactional variant — see [Work Manager](concepts/work.md).

```python
from pyuow.work.noop import NoOpWorkManager


work = NoOpWorkManager()

context = OrderContext(
    params=OrderParams(customer_id="42", sku="WIDGET", quantity=3)
)
result = work.by(flow).do_with(context)

confirmed = result.get()
print(confirmed)
# OrderConfirmed(customer_id='42', sku='WIDGET')
```

## Async variant

The same flow, async. Imports come from `pyuow.aio`, the units have `async def`, and the manager comes from `pyuow.work.aio.noop`.

```python
from pyuow.aio import (
    ConditionalUnit,
    ErrorUnit,
    FinalUnit,
    RunUnit,
)
from pyuow.work.aio.noop import NoOpWorkManager


class CheckStock(ConditionalUnit[OrderContext, OrderConfirmed]):
    async def condition(self, ctx: OrderContext) -> bool:
        ctx.in_stock = ctx.params.quantity <= 5
        return ctx.in_stock


# ... same shape for the other units, but with `async def`


work = NoOpWorkManager()
result = await work.by(flow).do_with(context)
```

## What's next?

- [Units & Flow](concepts/units.md) — full unit zoo and operator semantics
- [Result](concepts/result.md) — ok / error / empty, plus combinators
- [Domain Model](concepts/domain.md) — entities, batches, events
- [SQLAlchemy integration](integrations/sqlalchemy.md) — a real transactional manager
