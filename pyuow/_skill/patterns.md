# pyuow Patterns

Six canonical recipes. Each is the shortest working example of the pattern. Adapt freely.

---

## 1. Sync flow (no persistence)

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

---

## 2. Async flow (no persistence)

```python
import asyncio
from dataclasses import dataclass

from pyuow import BaseContext, BaseParams, Result
from pyuow.aio import ConditionalUnit, ErrorUnit, FinalUnit, RunUnit
from pyuow.work.aio.noop import NoOpWorkManager


@dataclass(frozen=True)
class Greeting(BaseParams):
    name: str


@dataclass
class Ctx(BaseContext[Greeting]):
    params: Greeting


class IsNamePresent(ConditionalUnit[Ctx, str]):
    async def condition(self, ctx: Ctx) -> bool:
        return bool(ctx.params.name)


class Greet(RunUnit[Ctx, str]):
    async def run(self, ctx: Ctx) -> None:
        print(f"Hello, {ctx.params.name}!")


class Done(FinalUnit[Ctx, str]):
    async def finish(self, ctx: Ctx) -> Result[str]:
        return Result.ok("greeted")


async def main() -> None:
    flow = (
        IsNamePresent(on_failure=ErrorUnit(exc=ValueError("name required")))
        >> Greet()
        >> Done()
    ).build()

    result = await NoOpWorkManager().by(flow).do_with(
        Ctx(params=Greeting(name="Alice"))
    )
    assert result.get() == "greeted"


asyncio.run(main())
```

---

## 3. Transactional flow with SQLAlchemy (sync)

Install first: `pip install "pyuow[sqlalchemy]"`.

```python
from sqlalchemy import create_engine

from pyuow.contrib.sqlalchemy import SqlAlchemyTransactionManager
from pyuow.work.transactional import TransactionalWorkManager

# Define flow as in pattern 1, then:

engine = create_engine("sqlite:///app.db")
work = TransactionalWorkManager(
    transaction_manager=SqlAlchemyTransactionManager(engine),
)

result = work.by(flow).do_with(Ctx(params=Greeting(name="Alice")))
# Commits on success, rolls back on failure (any unit returning Result.error).
```

---

## 4. Transactional flow with SQLAlchemy (async)

```python
from sqlalchemy.ext.asyncio import create_async_engine

from pyuow.contrib.sqlalchemy.aio import SqlAlchemyTransactionManager
from pyuow.work.aio.transactional import TransactionalWorkManager

# Define async flow as in pattern 2, then:

engine = create_async_engine("sqlite+aiosqlite:///app.db")
work = TransactionalWorkManager(
    transaction_manager=SqlAlchemyTransactionManager(engine),
)

result = await work.by(flow).do_with(Ctx(params=Greeting(name="Alice")))
```

---

## 5. Repository pattern (SQLAlchemy, sync)

```python
from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import DeclarativeBase

from pyuow.contrib.sqlalchemy import (
    BaseSqlAlchemyEntityRepository,
    BaseSqlAlchemyRepositoryFactory,
    EntityTable,
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)
from pyuow.entity import Entity


# 1. Define the entity
@dataclass
class Greeting(Entity[UUID]):
    name: str


# 2. Define the SQLAlchemy table mixin
class Base(DeclarativeBase):
    pass


class GreetingRecord(EntityTable, Base):
    __tablename__ = "greetings"
    name = Column(String(255), nullable=False)


# 3. Define the repository
class GreetingRepository(
    BaseSqlAlchemyEntityRepository[UUID, Greeting, GreetingRecord]
):
    def to_entity(self, record: GreetingRecord) -> Greeting:
        return Greeting(id=record.id, name=record.name)

    def to_record(self, entity: Greeting) -> GreetingRecord:
        return GreetingRecord(id=entity.id, name=entity.name)


# 4. Define the factory
class RepositoryFactory(BaseSqlAlchemyRepositoryFactory):
    @property
    def _repositories(self):
        return {Greeting: GreetingRepository(GreetingRecord)}


# 5. Wire it up
engine = create_engine("sqlite:///app.db")
factory = RepositoryFactory(
    transaction_manager=SqlAlchemyTransactionManager(engine),
    readonly_transaction_manager=SqlAlchemyReadOnlyTransactionManager(engine),
)
repo = factory.repo_for(Greeting)
repo.add(Greeting(id=uuid4(), name="Alice"))
found = repo.find(some_id)
```

For async: import from `pyuow.contrib.sqlalchemy.aio` and `pyuow.repository.aio`, use `create_async_engine`, and `await` the repo methods.

---

## 6. Domain batch handling

Use when you want changes to a domain `Batch` to be flushed automatically at the end of a flow.

```python
from dataclasses import dataclass, field

from pyuow import BaseParams
from pyuow.context.domain import BaseDomainContext
from pyuow.domain import Batch
from pyuow.work.transactional.domain import DomainTransactionalWorkManager

# Plus your existing SqlAlchemyTransactionManager and DomainRepository (see pyuow.repository.domain).


@dataclass(frozen=True)
class Params(BaseParams):
    user_id: str


@dataclass
class DomainCtx(BaseDomainContext[Params]):
    params: Params
    batch: Batch = field(default_factory=Batch)


# Inside a RunUnit, you mutate ctx.batch:
#   ctx.batch.add(some_aggregate)
#   ctx.batch.update(other_aggregate)
#   ctx.batch.delete(third_aggregate)

work = DomainTransactionalWorkManager(
    transaction_manager=SqlAlchemyTransactionManager(engine),
    batch_handler=domain_repository.process_batch,
)

result = work.by(flow).do_with(DomainCtx(params=Params(user_id="u1")))
# After the unit runs successfully, batch_handler is called with ctx.batch,
# then the transaction commits.
```

The batch handler is **only** invoked if the context inherits `BaseDomainContext`. For non-domain contexts, `DomainTransactionalWorkManager` behaves like `TransactionalWorkManager`.

---

## Picking the right work manager

| Use case | Manager |
|---|---|
| No transactions needed (tests, in-memory flows) | `NoOpWorkManager` |
| Single transaction per flow, commit/rollback | `TransactionalWorkManager` |
| Single transaction + flush domain `Batch` at end | `DomainTransactionalWorkManager` |

All three have the same `.by(flow).do_with(ctx)` shape and return `Result[T]`.
