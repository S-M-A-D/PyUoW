# SQLAlchemy

PyUoW ships a SQLAlchemy 2.x integration under `pyuow.contrib.sqlalchemy` (sync) and `pyuow.contrib.sqlalchemy.aio` (async). It provides:

- `SqlAlchemyTransactionManager` / `SqlAlchemyReadOnlyTransactionManager` — concrete transaction managers compatible with `TransactionalWorkManager`.
- `BaseSqlAlchemyEntityRepository` — implements `BaseEntityRepository` against any `EntityTable`.
- `BaseSqlAlchemyRepositoryFactory` — wires repositories together for use with `DomainTransactionalWorkManager`.
- `EntityTable` / `AuditedEntityTable` / `SoftDeletableEntityTable` / `VersionedEntityTable` — `DeclarativeBase` mixins that mirror the entity hierarchy.

Install the extra:

```bash
pip install "pyuow[sqlalchemy]"
```

---

## Define your tables

Use the table mixins to mirror the entity shape:

```python
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from pyuow.contrib.sqlalchemy.tables import AuditedEntityTable


class UserTable(AuditedEntityTable):
    __tablename__ = "users"
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
```

`AuditedEntityTable` already declares `id`, `created_date`, `updated_date`. `SoftDeletableEntityTable` adds `deleted_date`. `VersionedEntityTable` adds `version`. Mix-and-match by subclassing several.

---

## Define your entity

```python
from dataclasses import dataclass, replace
import typing as t
from uuid import UUID
from datetime import datetime

from pyuow.entity import AuditedEntity


UserId = t.NewType("UserId", UUID)


@dataclass(frozen=True)
class User(AuditedEntity[UserId]):
    name: str = ""
    email: str = ""

    def change_email(self, value: str) -> "User":
        return replace(self, email=value)
```

---

## Write the repository

Subclass `BaseSqlAlchemyEntityRepository` and provide the two converters between table rows and entities:

```python
from pyuow.contrib.sqlalchemy.repository import BaseSqlAlchemyEntityRepository


class UserRepository(
    BaseSqlAlchemyEntityRepository[UserId, User, UserTable]
):
    @staticmethod
    def to_entity(record: UserTable) -> User:
        return User(
            id=record.id,
            name=record.name,
            email=record.email,
            created_date=record.created_date,
            updated_date=record.updated_date,
        )

    @staticmethod
    def to_record(entity: User) -> UserTable:
        return UserTable(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            created_date=entity.created_date,
            updated_date=entity.updated_date,
        )
```

`BaseSqlAlchemyEntityRepository` gives you `find`, `find_all`, `get`, `exists`, `add`, `add_all`, `update`, `update_all`, `delete`, `delete_all` for free. Soft-deletion (when the entity inherits `SoftDeletableEntity`) is handled by `safe_select()` excluding `deleted_date IS NOT NULL` rows.

---

## Wire up the factory

```python
import typing as t
from pyuow.contrib.sqlalchemy.repository import BaseSqlAlchemyRepositoryFactory
from pyuow.entity import Entity
from pyuow.repository import BaseEntityRepository


class Repositories(BaseSqlAlchemyRepositoryFactory):
    @property
    def repositories(self) -> t.Mapping[
        t.Type[Entity[t.Any]],
        BaseEntityRepository[t.Any, t.Any],
    ]:
        return {
            User: UserRepository(
                UserTable,
                self._transaction_manager,
                self._readonly_transaction_manager,
            ),
        }

    def users(self) -> UserRepository:
        return t.cast(UserRepository, self.repo_for(User))
```

The factory exposes one explicit method per entity type for type-safe access.

---

## Run a transactional flow

```python
from sqlalchemy import create_engine

from pyuow import (
    BaseContext,
    BaseParams,
    FinalUnit,
    Result,
    RunUnit,
)
from pyuow.work.transactional import TransactionalWorkManager
from pyuow.contrib.sqlalchemy.work import (
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)
from dataclasses import dataclass
import typing as t
from uuid import uuid4


# Wire infrastructure
engine = create_engine("postgresql://postgres:postgres@localhost/postgres")

transaction_manager = SqlAlchemyTransactionManager(engine)
readonly_transaction_manager = SqlAlchemyReadOnlyTransactionManager(engine)

repositories = Repositories(
    transaction_manager=transaction_manager,
    readonly_transaction_manager=readonly_transaction_manager,
)

work = TransactionalWorkManager(transaction_manager=transaction_manager)


# Define the flow
@dataclass(frozen=True)
class CreateUserParams(BaseParams):
    name: str
    email: str


@dataclass
class CreateUserCtx(BaseContext[CreateUserParams]):
    params: CreateUserParams


class CreateUser(RunUnit[CreateUserCtx, UserId]):
    def __init__(self, *, users: UserRepository) -> None:
        super().__init__()
        self._users = users

    def run(self, ctx: CreateUserCtx) -> None:
        self._users.add(
            User(
                id=UserId(uuid4()),
                name=ctx.params.name,
                email=ctx.params.email,
            )
        )


class Done(FinalUnit[CreateUserCtx, UserId]):
    def finish(self, ctx: CreateUserCtx) -> Result[UserId]:
        return Result.ok(UserId(uuid4()))


flow = (CreateUser(users=repositories.users()) >> Done()).build()


# Run
ctx = CreateUserCtx(
    params=CreateUserParams(name="Alice", email="alice@example.com")
)
result = work.by(flow).do_with(ctx)
```

If the flow returns `Result.error(...)`, the transaction rolls back. If it returns `Result.ok(...)`, the transaction commits.

---

## With domain batching + events

Use `DomainTransactionalWorkManager` and a `DomainRepository` to combine the persistence pattern above with `Batch` + event dispatch:

```python
from pyuow.context.domain import BaseDomainContext
from pyuow.repository.domain import DomainRepository
from pyuow.work.transactional.domain import DomainTransactionalWorkManager


@dataclass(frozen=True)
class CreateUserCtx(BaseDomainContext[CreateUserParams]):
    params: CreateUserParams


class CreateUser(RunUnit[CreateUserCtx, UserId]):
    def run(self, ctx: CreateUserCtx) -> None:
        ctx.batch.add(
            User(name=ctx.params.name, email=ctx.params.email)
            # if User is a Model (event-emitting), id auto-generated
        )


def publish(events):
    for event in events:
        my_event_bus.publish(event)


domain_repo = DomainRepository(
    repositories=repositories,
    events_handler=publish,
)

work = DomainTransactionalWorkManager(
    transaction_manager=transaction_manager,
    batch_handler=domain_repo.process_batch,
)
```

The manager:

1. Runs the flow.
2. On success, calls `domain_repo.process_batch(ctx.batch)` *inside the transaction*.
3. That routes each `Change` to the right repository and dispatches all events via your `events_handler`.

---

## Async

The async surface mirrors the sync one. Imports change to `.aio`:

```python
from sqlalchemy.ext.asyncio import create_async_engine

from pyuow.contrib.sqlalchemy.aio.work import (
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)
from pyuow.contrib.sqlalchemy.aio.repository import (
    BaseSqlAlchemyEntityRepository,
    BaseSqlAlchemyRepositoryFactory,
)
from pyuow.work.aio.transactional import TransactionalWorkManager


engine = create_async_engine("postgresql+asyncpg://...")
transaction_manager = SqlAlchemyTransactionManager(engine)
work = TransactionalWorkManager(transaction_manager=transaction_manager)
```

Repository methods are `async`; tables and conversions remain the same.

---

## Nested transactions

`SqlAlchemyTransactionManager` automatically uses `session.begin_nested()` when an outer transaction is already active. This makes it safe to nest flows or call flows from inside other transactional code.

```python
with engine.connect() as conn, conn.begin():
    work.by(flow).do_with(ctx)   # uses a SAVEPOINT
```

---

## Read-only flows

`SqlAlchemyReadOnlyTransactionManager` switches the engine to `AUTOCOMMIT` and is the right manager for read paths in your repository. PyUoW's `BaseSqlAlchemyEntityRepository` uses it for `find`, `find_all`, `get`, `exists` automatically.

---

## Reference

- [`pyuow.contrib.sqlalchemy`](../api/contrib-sqlalchemy.md)
