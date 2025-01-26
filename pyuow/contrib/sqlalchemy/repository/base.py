import typing as t
from abc import ABC, abstractmethod
from dataclasses import asdict

from ....clock import offset_naive_utcnow
from ..tables import SoftDeletableEntityTable

try:
    from sqlalchemy import (
        ColumnElement,
        delete,
        exists,
        insert,
        select,
        update,
    )
except ImportError:  # pragma: no cover
    raise ImportError(
        "Seems that you are trying to import extra module that was not installed,"
        " please install pyuow[sqlalchemy]"
    )

from ....contrib.sqlalchemy.tables import (
    AuditedEntityTable,
    EntityTable,
    VersionedEntityTable,
)
from ....contrib.sqlalchemy.work.impl import (
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)
from ....entity import (
    AuditedEntity,
    Entity,
    SoftDeletableEntity,
    VersionedEntity,
)
from ....repository import BaseEntityRepository, BaseRepositoryFactory

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

    def find(self, entity_id: ENTITY_ID) -> t.Optional[ENTITY_TYPE]:
        statement = select(self._table).where(
            self._table.id == entity_id, *self._exclude_deleted()
        )

        with self._readonly_transaction_manager.transaction() as trx:
            result = (trx.it().execute(statement)).scalar_one_or_none()

        return self.to_entity(result) if result else None

    def find_all(
        self, entity_ids: t.Iterable[ENTITY_ID]
    ) -> t.Iterable[ENTITY_TYPE]:
        statement = select(self._table).where(
            self._table.id.in_(entity_ids), *self._exclude_deleted()
        )

        with self._readonly_transaction_manager.transaction() as trx:
            result = (trx.it().execute(statement)).scalars().all()

        return [self.to_entity(record) for record in result]

    def get(self, entity_id: ENTITY_ID) -> ENTITY_TYPE:
        statement = select(self._table).where(
            self._table.id == entity_id, *self._exclude_deleted()
        )

        with self._readonly_transaction_manager.transaction() as trx:
            result = (trx.it().execute(statement)).scalar_one()

        return self.to_entity(result)

    def exists(self, entity_id: ENTITY_ID) -> bool:
        statement = (
            exists(self._table)
            .where(self._table.id == entity_id, *self._exclude_deleted())
            .select()
        )

        with self._readonly_transaction_manager.transaction() as trx:
            return (trx.it().execute(statement)).scalar() or False

    def add(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
        statement = (
            insert(self._table)
            .values(**asdict(self.to_record(entity)))
            .returning(self._table)
        )

        with self._transaction_manager.transaction() as trx:
            result = (trx.it().execute(statement)).scalar_one()

        return self.to_entity(result)

    def add_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        return [self.add(entity) for entity in entities]

    def update(self, entity: ENTITY_TYPE) -> ENTITY_TYPE:
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

        with self._transaction_manager.transaction() as trx:
            result = (trx.it().execute(statement)).scalar_one()

        return self.to_entity(result)

    def update_all(
        self, entities: t.Sequence[ENTITY_TYPE]
    ) -> t.Iterable[ENTITY_TYPE]:
        return [self.update(entity) for entity in entities]

    def delete(self, entity: ENTITY_TYPE) -> bool:
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
                .where(self._table.id == entity.id, *self._exclude_deleted())
                .returning(self._table.id)
            )
            if isinstance(entity, SoftDeletableEntity)
            else (
                delete(self._table)
                .where(self._table.id == entity.id, *self._exclude_deleted())
                .returning(self._table.id)
            )
        )

        with self._transaction_manager.transaction() as trx:
            identifier = (trx.it().execute(statement)).scalar_one()

        return t.cast(bool, identifier == entity.id)

    def delete_all(self, entities: t.Sequence[ENTITY_TYPE]) -> bool:
        return all([self.update(entity) for entity in entities])

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
