# Domain Model

PyUoW ships a small but opinionated set of entity primitives plus a `Batch` collector and a `Model` base that emits events on creation and deletion.

---

## Entity hierarchy

```text
Entity[ID]
   ├── AuditedEntity[ID]        -- created_date, updated_date
   ├── SoftDeletableEntity[ID]  -- deleted_date
   └── VersionedEntity[ID]      -- version
                  │
                  └── (composed via mixins in your own subclasses or via Model)
```

All four are `@dataclass(frozen=True)`. They're imported from `pyuow.entity`:

```python
from dataclasses import dataclass
from uuid import UUID, uuid4
import typing as t

from pyuow.entity import AuditedEntity, Entity, SoftDeletableEntity, VersionedEntity, Version


UserId = t.NewType("UserId", UUID)


@dataclass(frozen=True)
class User(AuditedEntity[UserId], VersionedEntity[UserId]):
    name: str


user = User(id=UserId(uuid4()), name="Alice")
# created_date and updated_date are auto-filled to now (UTC, naive)
# version defaults to Version(0)
```

### Version

`Version` is an `int` subclass that refuses negatives and exposes `.next()`:

```python
from pyuow.entity import Version

v = Version(3)
v.next()       # Version(4)
Version(-1)    # raises ValueError
```

---

## Model — event-emitting entity

`Model[ID]` extends `AuditedEntity`, `SoftDeletableEntity`, and `VersionedEntity`. Every fresh instance auto-generates an id (via `_generate_id()`) and emits a `ModelCreatedEvent`. Calling `.delete()` emits a `ModelDeletedEvent`.

```python
from dataclasses import dataclass, replace
import datetime
import typing as t
from uuid import UUID, uuid4

from pyuow.domain import Model
from pyuow.domain.event import (
    ModelCreatedEvent,
    ModelDeletedEvent,
    ModelEvent,
)


OrderId = t.NewType("OrderId", UUID)


@dataclass(frozen=True)
class OrderCreated(ModelCreatedEvent[OrderId]):
    sku: str


@dataclass(frozen=True)
class OrderDeleted(ModelDeletedEvent[OrderId]):
    pass


@dataclass(frozen=True)
class OrderUpdated(ModelEvent[OrderId]):
    new_quantity: int


@dataclass(frozen=True)
class Order(Model[OrderId]):
    sku: str = ""
    quantity: int = 0

    def _generate_id(self) -> OrderId:
        return OrderId(uuid4())

    def _created_event(self, date: datetime.datetime) -> OrderCreated:
        return OrderCreated(
            id=uuid4(),
            model_id=self.id,
            sku=self.sku,
            created_date=date,
        )

    def _deleted_event(self, date: datetime.datetime) -> OrderDeleted:
        return OrderDeleted(
            id=uuid4(), model_id=self.id, deleted_date=date
        )

    def change_quantity(self, new_quantity: int) -> "Order":
        return self.update(
            event=OrderUpdated(
                id=uuid4(), model_id=self.id, new_quantity=new_quantity
            ),
            quantity=new_quantity,
        )
```

### Lifecycle

```python
# Fresh model -> is_new=True, has a created event
order = Order(sku="WIDGET", quantity=3)
order.is_new           # True
order.events()         # (OrderCreated(...),)

# Mutate via .update() -> immutable replace + appended event
ordered = order.change_quantity(5)
ordered.events()       # (OrderCreated(...), OrderUpdated(new_quantity=5))

# Delete -> sets deleted_date + appends a deleted event
canceled = ordered.delete()
canceled.is_deleted    # True
canceled.events()      # (... OrderDeleted(...))
```

`events()` returns an immutable tuple. Each call returns a fresh tuple over the same event objects (events are frozen, no defensive copy needed).

---

## Batch — collecting changes

`Batch` is a per-flow accumulator. Units call `batch.add(entity)`, `batch.update(entity)`, `batch.delete(entity)` as they go. The Work Manager flushes the batch at the end of the transaction.

```python
from pyuow.domain import Batch

batch = Batch()
batch.add(Order(sku="WIDGET", quantity=3))   # ADD change for a new model
batch.update(existing_order)                  # UPDATE change
batch.delete(canceled_order)                  # DELETE change

batch.changes()    # dict keyed by entity.id, values are Change records
batch.events()     # tuple of all events from all Models in the batch
```

### Batch rules

The batch enforces operation ordering invariants. Violations raise specific exceptions from `pyuow.domain`:

| Violation                                              | Exception                          |
| ------------------------------------------------------ | ---------------------------------- |
| `.add()` on a `Model` that's already persisted         | `CannotAddExistingEntityError`     |
| `.update()` on a fresh `Model`                         | `CannotUpdateNewEntityError`       |
| `.delete()` on a fresh `Model`                         | `CannotDeleteNewEntityError`       |
| Any mutation after `.shut()`                           | `BatchShutError`                   |
| Same entity id added twice                             | `DuplicateEntityInBatchError`      |

All five inherit from `BatchError`, so catching the parent covers all cases.

---

## Batch and Domain Context

`BaseDomainContext` is a `BaseContext` with a `batch: Batch` field built in. Combine it with `DomainTransactionalWorkManager` and the batch flushes automatically.

```python
from dataclasses import dataclass
from pyuow.context.domain import BaseDomainContext


@dataclass(frozen=True)
class OrderParams(BaseParams):
    sku: str


@dataclass(frozen=True)
class OrderCtx(BaseDomainContext[OrderParams]):
    params: OrderParams
```

Inside a `RunUnit`, append to the batch:

```python
class CreateOrder(RunUnit[OrderCtx, OrderResult]):
    def run(self, ctx: OrderCtx) -> None:
        ctx.batch.add(Order(sku=ctx.params.sku, quantity=1))
```

The manager calls your `batch_handler` after the flow finishes — see [Work Manager](work.md#domaintransactionalworkmanager).

---

## Events

### ModelEvent

`ModelEvent[ID]` is the base class for domain events emitted by a `Model`. Required fields:

- `id: UUID` — event identity
- `model_id: ID` — the entity it belongs to
- `occurred_at: int` — nanosecond UTC timestamp (auto-filled from `pyuow.clock.nano_timestamp_utc`)

```python
from dataclasses import dataclass
from pyuow.domain.event import ModelEvent


@dataclass(frozen=True)
class OrderShipped(ModelEvent[OrderId]):
    tracking_number: str
```

### ModelCreatedEvent / ModelDeletedEvent

Two ready-made subclasses with `created_date` / `deleted_date` fields. Used by `Model._created_event()` and `Model._deleted_event()` respectively.

### EventHandler

`pyuow.domain.event.EventHandler` is a protocol-style ABC for the consumer side:

```python
import typing as t
from pyuow.domain.event import EventHandler, ModelEvent


class MyEventBus(EventHandler):
    def __call__(self, events: t.Sequence[ModelEvent[t.Any]]) -> None:
        for event in events:
            self._publish(event)
```

An async version lives at `pyuow.domain.aio.event.EventHandler` with `async def __call__`.

---

## Reference

- [`pyuow.entity`](../api/entity.md)
- [`pyuow.domain`](../api/domain.md)
