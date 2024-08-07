import typing as t
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime

try:
    from sqlalchemy import delete, exists, insert, select, update
except ImportError:  # pragma: no cover
    raise ImportError(
        "Seems that you are trying to import extra module that was not installed,"
        " please install pyuow[sqlalchemy]"
    )

from ......persistence.aio.repository import (
    BaseEntityRepository,
    BaseRepositoryFactory,
)
from ......persistence.entity import Entity
from ....persistence.tables import AuditedEntityTable, EntityTable
from ...work.impl import (
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Any)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound=Entity[t.Any])
ENTITY_TABLE = t.TypeVar("ENTITY_TABLE", bound=EntityTable)


class BaseSqlAlchemyEntityRepository(
    BaseEntityRepository[ENTITY_ID, ENTITY_TYPE],
    t.Generic[ENTITY_ID, ENTITY_TYPE, ENTITY_TABLE],
    ABC,
):
    def __init__(
        self,
        table: t.Type[ENTITY_TABLE],
        transaction_manager: SqlAlchemyTransactionManager,
        readonly_transaction_manager: SqlAlchemyReadOnlyTransactionManager,
    ) -> None:
        self._table = table
        self._transaction_manager = transaction_manager
        self._readonly_transaction_manager = readonly_transaction_manager

    @staticmethod
    @abstractmethod
    def to_entity(record: ENTITY_TABLE) -> ENTITY_TYPE:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_record(entity: ENTITY_TYPE) -> ENTITY_TABLE:
        raise NotImplementedError

    async def find(self, entity_id: ENTITY_ID) -> t.Optional[ENTITY_TYPE]:
        statement = select(self._table).where(self._table.id == entity_id)

        async with self._readonly_transaction_manager.transaction() as trx:
            result = (await trx.it().execute(statement)).scalar_one_or_none()

        return self.to_entity(result) if result else None

    async def find_all(
        self, entity_ids: t.Iterable[ENTITY_ID]
    ) -> t.Iterable[ENTITY_TYPE]:
        statement = select(self._table).where(self._table.id.in_(entity_ids))

        async with self._readonly_transaction_manager.transaction() as trx:
            result = (await trx.it().execute(statement)).scalars().all()

        return [self.to_entity(record) for record in result]

    async def get(self, entity_id: ENTITY_ID) -> ENTITY_TYPE:
        statement = select(self._table).where(self._table.id == entity_id)

        async with self._readonly_transaction_manager.transaction() as trx:
            result = (await trx.it().execute(statement)).scalar_one()

        return self.to_entity(result)

    async def exists(self, entity_id: ENTITY_ID) -> bool:
        statement = (
            exists(self._table).where(self._table.id == entity_id).select()
        )

        async with self._readonly_transaction_manager.transaction() as trx:
            return (await trx.it().execute(statement)).scalar() or False

    async def add(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        statement = (
            insert(self._table)
            .values(**asdict(self.to_record(entity)))
            .returning(self._table)
        )

        async with self._transaction_manager.transaction() as trx:
            result = (await trx.it().execute(statement)).scalar_one()

        return self.to_entity(result)

    async def add_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        return [await self.add(entity) for entity in entities]

    async def update(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        record = self.to_record(entity)

        if isinstance(record, AuditedEntityTable):
            record.updated_date = datetime.utcnow()

        statement = (
            update(self._table)
            .values(**asdict(record))
            .where(self._table.id == entity.id)
            .returning(self._table)
        )

        async with self._transaction_manager.transaction() as trx:
            result = (await trx.it().execute(statement)).scalar_one()

        return self.to_entity(result)

    async def update_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        return [await self.update(entity) for entity in entities]

    async def delete(self, entity: ENTITY_TYPE) -> bool:
        statement = (
            delete(self._table)
            .where(self._table.id == entity.id)
            .returning(self._table.id)
        )

        async with self._transaction_manager.transaction() as trx:
            identifier = (await trx.it().execute(statement)).scalar_one()

        return t.cast(bool, identifier == entity.id)


class BaseSqlAlchemyRepositoryFactory(BaseRepositoryFactory, ABC):
    def __init__(
        self,
        transaction_manager: SqlAlchemyTransactionManager,
        readonly_transaction_manager: SqlAlchemyReadOnlyTransactionManager,
    ) -> None:
        self._transaction_manager = transaction_manager
        self._readonly_transaction_manager = readonly_transaction_manager
