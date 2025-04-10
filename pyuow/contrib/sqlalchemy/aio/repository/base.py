import typing as t
from abc import ABC, abstractmethod
from dataclasses import asdict

from .....clock import offset_naive_utcnow
from ...tables import SoftDeletableEntityTable

try:
    from sqlalchemy import (
        ColumnElement,
        delete,
        exists,
        insert,
        select,
        update,
    )
    from sqlalchemy.sql.selectable import Select
except ImportError:  # pragma: no cover
    raise ImportError(
        "Seems that you are trying to import extra module that was not installed,"
        " please install pyuow[sqlalchemy]"
    )

from .....contrib.sqlalchemy.aio.work.impl import (
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)
from .....contrib.sqlalchemy.tables import (
    AuditedEntityTable,
    EntityTable,
    VersionedEntityTable,
)
from .....entity import (
    AuditedEntity,
    Entity,
    SoftDeletableEntity,
    VersionedEntity,
)
from .....repository.aio import BaseEntityRepository, BaseRepositoryFactory

ENTITY_ID = t.TypeVar("ENTITY_ID", bound=t.Any)
ENTITY_TYPE = t.TypeVar("ENTITY_TYPE", bound=Entity[t.Any])
ENTITY_TABLE = t.TypeVar("ENTITY_TABLE", bound=EntityTable)


class BaseSqlAlchemyEntityRepository(
    t.Generic[ENTITY_ID, ENTITY_TYPE, ENTITY_TABLE],
    BaseEntityRepository[ENTITY_ID, ENTITY_TYPE],
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
        statement = self.safe_select().where(self._table.id == entity_id)

        async with self._readonly_transaction_manager.transaction() as trx:
            result = (await trx.it().execute(statement)).scalar_one_or_none()

        return self.to_entity(result) if result else None

    async def find_all(
        self, entity_ids: t.Iterable[ENTITY_ID]
    ) -> t.Iterable[ENTITY_TYPE]:
        statement = self.safe_select().where(self._table.id.in_(entity_ids))

        async with self._readonly_transaction_manager.transaction() as trx:
            result = (await trx.it().execute(statement)).scalars().all()

        return [self.to_entity(record) for record in result]

    async def get(self, entity_id: ENTITY_ID) -> ENTITY_TYPE:
        statement = self.safe_select().where(self._table.id == entity_id)

        async with self._readonly_transaction_manager.transaction() as trx:
            result = (await trx.it().execute(statement)).scalar_one()

        return self.to_entity(result)

    async def exists(self, entity_id: ENTITY_ID) -> bool:
        statement = (
            exists(self._table)
            .where(self._table.id == entity_id, *self._exclude_deleted())
            .select()
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
        conditions = self._exclude_deleted()

        if (
            isinstance(record, AuditedEntityTable)
            and issubclass(self._table, AuditedEntityTable)
            and isinstance(entity, AuditedEntity)
        ):
            record.updated_date = offset_naive_utcnow()
            conditions.append(self._table.created_date == entity.created_date)
            conditions.append(self._table.updated_date == entity.updated_date)

        if (
            isinstance(record, VersionedEntityTable)
            and issubclass(self._table, VersionedEntityTable)
            and isinstance(entity, VersionedEntity)
        ):
            record.version = entity.version.next()
            conditions.append(self._table.version == entity.version)

        statement = (
            update(self._table)
            .values(**asdict(record))
            .where(self._table.id == entity.id, *conditions)
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
            (
                update(self._table)
                .values(
                    deleted_date=(
                        entity.deleted_date
                        if entity.deleted_date
                        else offset_naive_utcnow()
                    )
                )
                .where(self._table.id == entity.id)
                .returning(self._table.id)
            )
            if isinstance(entity, SoftDeletableEntity)
            else (
                delete(self._table)
                .where(self._table.id == entity.id)
                .returning(self._table.id)
            )
        )

        async with self._transaction_manager.transaction() as trx:
            identifier = (await trx.it().execute(statement)).scalar_one()

        return t.cast(bool, identifier == entity.id)

    async def delete_all(self, entities: t.Sequence[ENTITY_TYPE]) -> bool:
        return all([await self.update(entity) for entity in entities])

    def safe_select(self) -> Select[t.Any]:
        return select(self._table).where(*self._exclude_deleted())

    def _exclude_deleted(self) -> t.List[ColumnElement[bool]]:
        conditions: t.List[ColumnElement[bool]] = []

        if issubclass(self._table, SoftDeletableEntityTable):
            conditions.append(self._table.deleted_date == None)

        return conditions


class BaseSqlAlchemyRepositoryFactory(BaseRepositoryFactory, ABC):
    def __init__(
        self,
        transaction_manager: SqlAlchemyTransactionManager,
        readonly_transaction_manager: SqlAlchemyReadOnlyTransactionManager,
    ) -> None:
        self._transaction_manager = transaction_manager
        self._readonly_transaction_manager = readonly_transaction_manager
