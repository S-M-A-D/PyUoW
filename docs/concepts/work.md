# Work Manager

A **Work Manager** runs a flow and wraps it with cross-cutting concerns: transactions, batch flushing, event dispatch. It is the "Unit of Work" half of PyUoW.

The pattern:

```python
result = work.by(flow).do_with(context)
```

`work.by(flow)` returns a *proxy* (a `BaseUnitProxy`) that adapts the flow to the manager's lifecycle. `.do_with(context)` invokes the proxy.

PyUoW ships four managers.

---

## NoOpWorkManager

The simplest — just runs the flow. Useful for tests, scripts, and code that doesn't need transactional semantics.

```python
from pyuow.work.noop import NoOpWorkManager

work = NoOpWorkManager()
result = work.by(flow).do_with(context)
```

Async twin: `pyuow.work.aio.noop.NoOpWorkManager`.

---

## TransactionalWorkManager

Wraps the flow in a transaction. Commits on success, rolls back if the flow returns `Result.error(...)`.

```python
from pyuow.work.transactional import TransactionalWorkManager
from pyuow.contrib.sqlalchemy.work import SqlAlchemyTransactionManager
from sqlalchemy import create_engine

engine = create_engine("postgresql://...")
transaction_manager = SqlAlchemyTransactionManager(engine)
work = TransactionalWorkManager(transaction_manager=transaction_manager)

result = work.by(flow).do_with(context)
```

The `transaction_manager` is the backend-specific bit. PyUoW provides one for SQLAlchemy out of the box — see [SQLAlchemy integration](../integrations/sqlalchemy.md). You can implement your own by subclassing `BaseTransactionManager`.

Async twin: `pyuow.work.aio.transactional.TransactionalWorkManager` with `pyuow.contrib.sqlalchemy.aio.work.SqlAlchemyTransactionManager`.

---

## DomainTransactionalWorkManager

Extends the transactional manager with **domain batch flushing**. If the context is a `BaseDomainContext`, the manager calls a `batch_handler` you provide *after* the flow finishes successfully and *inside* the transaction.

```python
from pyuow.work.transactional.domain import DomainTransactionalWorkManager
from pyuow.context.domain import BaseDomainContext
from pyuow.domain import Batch


def flush_batch(batch: Batch) -> None:
    """Iterate batch.changes() / batch.events() and persist them."""
    ...


work = DomainTransactionalWorkManager(
    transaction_manager=transaction_manager,
    batch_handler=flush_batch,
)

@dataclass
class OrderContext(BaseDomainContext[OrderParams]):
    params: OrderParams


result = work.by(flow).do_with(OrderContext(params=OrderParams(...)))
```

A typical `batch_handler` looks like a [`DomainRepository`](#using-domainrepository-as-the-batch-handler) (see below).

Async twin: `pyuow.work.aio.transactional.domain.DomainTransactionalWorkManager`.

---

## Using `DomainRepository` as the batch handler

`pyuow.repository.domain.DomainRepository` (and its aio counterpart) is the canonical batch handler. It:

1. Reads `batch.changes()` and dispatches each `Change` to the right repository.
2. Reads `batch.events()` and passes them to your event handler.

```python
from pyuow.repository.domain import DomainRepository


domain_repo = DomainRepository(
    repositories=repositories_factory,
    events_handler=lambda events: my_event_bus.publish(events),
)

work = DomainTransactionalWorkManager(
    transaction_manager=transaction_manager,
    batch_handler=domain_repo.process_batch,
)
```

`repositories_factory` is your `BaseRepositoryFactory`. See [SQLAlchemy integration](../integrations/sqlalchemy.md) for a full example.

---

## Choosing a manager

| You need                                              | Use                              |
| ----------------------------------------------------- | -------------------------------- |
| Run a flow, no persistence                            | `NoOpWorkManager`                |
| Run a flow inside a DB transaction                    | `TransactionalWorkManager`       |
| Run a flow + flush a Batch of entities + emit events  | `DomainTransactionalWorkManager` |

---

## Implementing a custom manager

Subclass `BaseWorkManager` and `BaseUnitProxy`. The proxy's `__call__` is your chance to wrap the unit invocation:

```python
from pyuow.work import BaseUnitProxy, BaseWorkManager
from pyuow.unit import BaseUnit


class LoggingUnitProxy(BaseUnitProxy[CONTEXT, OUT]):
    def __init__(self, *, unit: BaseUnit[CONTEXT, OUT]) -> None:
        self._unit = unit

    def __call__(self, context: CONTEXT) -> Result[OUT]:
        logger.info("running unit %s", self._unit.__class__.__name__)
        return self._unit(context)


class LoggingWorkManager(BaseWorkManager):
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseUnitProxy[CONTEXT, OUT]:
        return LoggingUnitProxy(unit=unit)
```

## Reference

- [`pyuow.work`](../api/work.md)
