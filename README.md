<p align="center">
  <a href="https://github.com/S-M-A-D/PyUoW"><img src="https://raw.githubusercontent.com/S-M-A-D/PyUoW/main/static/logo.png" alt="pyUoW" width="500"></a>
</p>
<p align="center">
    <em>Unit of Work: A Behavioral Pattern in Software Development Implemented in Python.</em>
<p align="center">
    <a href="https://pepy.tech/project/pyuow" target="_blank">
        <img src="https://static.pepy.tech/badge/pyuow" alt="Downloads">
    </a>
    <a href="https://github.com/S-M-A-D/PyUoW/actions/workflows/build.yaml" target="_blank">
        <img src="https://github.com/S-M-A-D/PyUoW/actions/workflows/build.yaml/badge.svg" alt="Build">
    </a>
    <a href="https://codecov.io/gh/S-M-A-D/PyUoW" target="_blank">
        <img src="https://codecov.io/gh/S-M-A-D/PyUoW/graph/badge.svg?token=L1Y13VT30W" alt="Codecov">
    </a>
    <img src="https://img.shields.io/badge/code%20style-black-black" alt="Formatter">
    <img src="https://img.shields.io/pypi/pyversions/pyuow" alt="Python versions">
    <img src="https://img.shields.io/pypi/l/pyuow" alt="License">
</p>

---

## Table of Contents

1. [Installation](#installation)
2. [Usage examples](#usage-examples)
   - [Simple unit](#simple-unit-usage-example)
   - [Unit of Work manager](#example-with-unit-of-work-manager)
   - [SqlAlchemy based Unit of Work manager](#example-with-sqlalchemy-based-unit-of-work-manager)
3. [Async compatibility](#async-compatibility)
4. [Contributors guide](#for-pyuow-contributors)

---

## Installation

PyUow package is available on PyPI:
```console
$ python -m pip install pyuow
```
PyUow officially supports Python >= 3.9.

PyPi link -

---

## Usage examples

### Simple unit usage example:

#### Definition:
```python
import typing as t
from dataclasses import dataclass

from pyuow.aio import (
   ConditionalUnit,
   RunUnit,
   FinalUnit,
   ErrorUnit,
)
from pyuow import (
    BaseContext,
    Result,
)


@dataclass(frozen=True)
class ExampleParams:
    field: str


@dataclass
class ExampleContext(BaseContext[ExampleParams]):
    field: str


@dataclass(frozen=True)
class ExampleOutput:
    field: str


class ExampleConditionalUnit(ConditionalUnit[ExampleContext, ExampleOutput]):
    async def condition(
        self, context: ExampleContext, **kwargs: t.Any
    ) -> bool:
        return context.field == "context field value"


class ExampleRunUnit(RunUnit[ExampleContext, ExampleOutput]):
    async def run(self, context: ExampleContext, **kwargs: t.Any) -> None:
        print(
            f"I'm just running a logic, and displaying: {context.params.field}"
        )


class SuccessUnit(FinalUnit[ExampleContext, ExampleOutput]):
    async def finish(
        self, context: ExampleContext, **kwargs: t.Any
    ) -> Result[ExampleOutput]:
        return Result.ok(ExampleOutput(field="success"))


flow = (
    ExampleConditionalUnit(
        on_failure=ErrorUnit(exc=Exception("example error"))
    )
    >> ExampleRunUnit()
    >> SuccessUnit()
).build()
```

#### Success scenario:
```python
async def main() -> None:
    params = ExampleParams(field="params field value")
    context = ExampleContext(params=params, field="context field value")
    result = await flow(context)
    result.get()
```

#### Failure scenario:
```python
async def main() -> None:
    params = ExampleParams(field="params field value")
    context = ExampleContext(params=params, field="invalid field value")
    result = await flow(context)
    result.get()
```

### Example with Unit of Work manager

:warning: NoOp - No Operations, can be replaced with your own implementation of UoW.

```python
...
from pyuow.work.noop import NoOpWorkManager

...

work = NoOpWorkManager()

...

async def main() -> None:
    ...
    result = await work.by(flow).do_with(context)
    ...
```

### Example with SqlAlchemy based Unit of Work manager:

```python
from __future__ import annotations

import typing as t
from dataclasses import dataclass, replace
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Mapped

from pyuow.aio import (
   ConditionalUnit,
   RunUnit,
   FinalUnit,
   ErrorUnit,
)
from pyuow import (
   BaseContext,
   Result,
)

from pyuow.contrib.sqlalchemy.tables import AuditedEntityTable
from pyuow.contrib.sqlalchemy.aio.repository import (
   BaseSqlAlchemyRepositoryFactory,
   BaseSqlAlchemyEntityRepository,
)
from pyuow.contrib.sqlalchemy.aio.work import (
   SqlAlchemyReadOnlyTransactionManager,
   SqlAlchemyTransactionManager,
)
from pyuow.persistence.entities import Entity, AuditedEntity
from pyuow.repository.aio import BaseEntityRepository
from pyuow.work.aio.transactional import TransactionalWorkManager

ExampleEntityId = t.NewType("ExampleEntityId", UUID)


@dataclass(frozen=True, kw_only=True)
class ExampleAuditedEntity(AuditedEntity[ExampleEntityId]):
   field: str

   def change_field(self, value: str) -> ExampleAuditedEntity:
      return replace(self, field=value)


class ExampleEntityTable(AuditedEntityTable):
   __tablename__ = "example_entities"

   field: Mapped[str]


class ExampleEntityRepository(
   BaseSqlAlchemyEntityRepository[
      ExampleEntityId, ExampleAuditedEntity, ExampleEntityTable
   ]
):
   @staticmethod
   def to_entity(record: ExampleEntityTable) -> ExampleAuditedEntity:
      return ExampleAuditedEntity(
         id=record.id,
         field=record.field,
         created_date=record.created_date,
         updated_date=record.updated_date,
      )

   @staticmethod
   def to_record(entity: ExampleAuditedEntity) -> ExampleEntityTable:
      return ExampleEntityTable(
         id=entity.id,
         field=entity.field,
         created_date=entity.created_date,
         updated_date=entity.updated_date,
      )


class ExampleRepositoryFactory(BaseSqlAlchemyRepositoryFactory):
   @property
   def repositories(self) -> t.Mapping[
      t.Type[Entity[t.Any]],
      BaseEntityRepository[t.Any, t.Any],
   ]:
      return {
         ExampleAuditedEntity: ExampleEntityRepository(
            ExampleEntityTable,
            self._transaction_manager,
            self._readonly_transaction_manager,
         ),
      }

   def example_entity_repository(self) -> ExampleEntityRepository:
      return t.cast(
         ExampleEntityRepository,
         repositories.repo_for(ExampleAuditedEntity),
      )


@dataclass(frozen=True)
class ExampleParams:
   field: str


@dataclass
class ExampleContext(BaseContext[ExampleParams]):
   field: str


@dataclass(frozen=True)
class ExampleOutput:
   field: str


class ExampleConditionalUnit(ConditionalUnit[ExampleContext, ExampleOutput]):
   async def condition(
           self, context: ExampleContext, **kwargs: t.Any
   ) -> bool:
      return context.field == "context field value"


class ExampleRunUnit(RunUnit[ExampleContext, ExampleOutput]):
   def __init__(
           self, *, example_entity_repository: ExampleEntityRepository
   ) -> None:
      super().__init__()
      self._example_entity_repository = example_entity_repository

   async def run(self, context: ExampleContext, **kwargs: t.Any) -> None:
      entity = ExampleAuditedEntity(
         id=ExampleEntityId(str(uuid4())), field=context.params.field
      )
      await self._example_entity_repository.add(entity)


class SuccessUnit(FinalUnit[ExampleContext, ExampleOutput]):
   async def finish(
           self, context: ExampleContext, **kwargs: t.Any
   ) -> Result[ExampleOutput]:
      return Result.ok(ExampleOutput(field="success"))


engine = create_async_engine("postgresql://postgres:postgres@db:5432/postgres")

transaction_manager = SqlAlchemyTransactionManager(engine)
readonly_transaction_manager = SqlAlchemyReadOnlyTransactionManager(engine)

repositories = ExampleRepositoryFactory(
   transaction_manager=transaction_manager,
   readonly_transaction_manager=readonly_transaction_manager,
)

work = TransactionalWorkManager(transaction_manager=transaction_manager)

flow = (
        ExampleConditionalUnit(
           on_failure=ErrorUnit(exc=Exception("example error"))
        )
        >> ExampleRunUnit(
   example_entity_repository=repositories.example_entity_repository()
)
        >> SuccessUnit()
).build()


async def main() -> None:
   params = ExampleParams(field="params field value")
   context = ExampleContext(params=params, field="context field value")
   result = await work.by(flow).do_with(context)
   result.get()

```
## Async compatibility
This package provides robust support for both asynchronous (async) and synchronous (sync) versions of code execution, catering to diverse development needs.
The package follows the convention where each module with async code has an aio/ folder in the same directory, allowing you to easily import the async version.

For example:

```python
# Async code imports
from pyuow.aio import (
   ConditionalUnit,
   RunUnit,
   FinalUnit,
   ErrorUnit,
)
from pyuow import (
   BaseContext,
   Result,
)
from pyuow.repository.aio.base import (
   BaseEntityRepository
)

# Sync code imports
from pyuow import (
   BaseContext,
   Result,
   ConditionalUnit,
   RunUnit,
   FinalUnit,
   ErrorUnit,
)
from pyuow.repository import (
   BaseEntityRepository
)
```
Same with contributing modules:
```python
# Async code imports
from pyuow.contrib.sqlalchemy.aio.work.impl import (
   SqlAlchemyTransaction,
   SqlAlchemyReadOnlyTransactionManager,
)

# Sync code imports
from pyuow.contrib.sqlalchemy.work.impl import (
   SqlAlchemyTransaction,
   SqlAlchemyReadOnlyTransactionManager,
)
```
---

## For PyUoW contributors:
For guidance on setting up a development environment and how to make a contribution to PyUow,
please see [CONTRIBUTING.md](https://github.com/S-M-A-D/PyUoW/blob/main/CONTRIBUTING.md) for more information.
