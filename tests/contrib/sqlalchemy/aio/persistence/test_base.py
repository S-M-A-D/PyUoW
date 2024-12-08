from __future__ import annotations

import typing as t
from dataclasses import dataclass, replace
from uuid import uuid4

import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine

from pyuow.contrib.sqlalchemy.aio.repository import (
    BaseSqlAlchemyEntityRepository,
    BaseSqlAlchemyRepositoryFactory,
)
from pyuow.contrib.sqlalchemy.aio.work import (
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)
from pyuow.entity import AuditedEntity, Entity
from pyuow.repository.aio import BaseEntityRepository
from pyuow.types import MISSING

from ...faked_entities import (
    FakeAuditedEntityTable,
    FakeEntityId,
    FakeEntityTable,
)


@dataclass(frozen=True)
class FakeAuditedEntity(AuditedEntity[FakeEntityId]):
    field: str = t.cast(t.Any, MISSING)

    def change_field(self, value: str) -> FakeAuditedEntity:
        return replace(self, field=value)


@dataclass(frozen=True)
class FakeEntity(Entity[FakeEntityId]):
    field: str = t.cast(t.Any, MISSING)

    def change_field(self, value: str) -> FakeEntity:
        return replace(self, field=value)


class FakeEntityRepository(
    BaseSqlAlchemyEntityRepository[FakeEntityId, FakeEntity, FakeEntityTable]
):
    @staticmethod
    def to_entity(record: FakeEntityTable) -> FakeEntity:
        return FakeEntity(
            id=FakeEntityId(record.id),
            field=record.field,
        )

    @staticmethod
    def to_record(entity: FakeEntity) -> FakeEntityTable:
        return FakeEntityTable(
            id=entity.id,
            field=entity.field,
        )


class FakeAuditedEntityRepository(
    BaseSqlAlchemyEntityRepository[
        FakeEntityId, FakeAuditedEntity, FakeAuditedEntityTable
    ]
):
    @staticmethod
    def to_entity(record: FakeAuditedEntityTable) -> FakeAuditedEntity:
        return FakeAuditedEntity(
            id=FakeEntityId(record.id),
            field=record.field,
            created_date=record.created_date,
            updated_date=record.updated_date,
        )

    @staticmethod
    def to_record(entity: FakeAuditedEntity) -> FakeAuditedEntityTable:
        return FakeAuditedEntityTable(
            id=entity.id,
            field=entity.field,
            created_date=entity.created_date,
            updated_date=entity.updated_date,
        )


class FakeRepositoryFactory(BaseSqlAlchemyRepositoryFactory):
    @property
    def repositories(self) -> t.Mapping[
        t.Type[Entity[t.Any]],
        BaseEntityRepository[t.Any, t.Any],
    ]:
        return {
            FakeAuditedEntity: FakeAuditedEntityRepository(
                FakeAuditedEntityTable,
                self._transaction_manager,
                self._readonly_transaction_manager,
            ),
            FakeEntity: FakeEntityRepository(
                FakeEntityTable,
                self._transaction_manager,
                self._readonly_transaction_manager,
            ),
        }


@pytest.fixture
def repository_factory(async_engine: AsyncEngine) -> FakeRepositoryFactory:
    return FakeRepositoryFactory(
        transaction_manager=SqlAlchemyTransactionManager(async_engine),
        readonly_transaction_manager=SqlAlchemyReadOnlyTransactionManager(
            async_engine
        ),
    )


@pytest.mark.skip_on_ci
class TestSqlAlchemyEntityRepository:
    @pytest.fixture
    def audited_entity_repository(
        self, repository_factory: FakeRepositoryFactory
    ) -> BaseEntityRepository[FakeEntityId, FakeAuditedEntity]:
        return repository_factory.repo_for(FakeAuditedEntity)

    @pytest.fixture
    def entity_repository(
        self, repository_factory: FakeRepositoryFactory
    ) -> BaseEntityRepository[FakeEntityId, FakeEntity]:
        return repository_factory.repo_for(FakeEntity)

    async def test_async_find_should_find_entity(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        await audited_entity_repository.add(entity)
        # when
        result = await audited_entity_repository.find(entity.id)
        # then
        assert result == entity

    async def test_async_find_all_should_find_all_entities(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity1 = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        entity2 = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        await audited_entity_repository.add_all([entity1, entity2])
        # when
        result = await audited_entity_repository.find_all(
            [entity1.id, entity2.id]
        )
        # then
        assert {e for e in result} == {entity1, entity2}

    async def test_async_get_should_get_existing_entity(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        await audited_entity_repository.add(entity)
        # when
        result = await audited_entity_repository.get(entity.id)
        # then
        assert result == entity

    async def test_async_get_should_raise_if_no_entity_exists(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity_id = FakeEntityId(uuid4())
        # when / then
        with pytest.raises(NoResultFound):
            await audited_entity_repository.get(entity_id)

    async def test_async_exists_should_return_true_if_entity_exists(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        await audited_entity_repository.add(entity)
        # when
        result = await audited_entity_repository.exists(entity.id)
        # then
        assert result is True

    async def test_async_exists_should_return_false_if_no_entity_found(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity_id = FakeEntityId(uuid4())
        # when
        result = await audited_entity_repository.exists(entity_id)
        # then
        assert result is False

    async def test_async_update_non_audited_entity_should_update_both_entity_and_date(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        await audited_entity_repository.add(entity)
        # when
        result = await audited_entity_repository.update(
            entity.change_field("changed")
        )
        # then
        assert result.field == "changed"
        assert result.updated_date > entity.updated_date

    async def test_async_update_non_audited_entity_should_update_only_entity(
        self, entity_repository: FakeEntityRepository
    ) -> None:
        # given
        entity = FakeEntity(id=FakeEntityId(uuid4()), field="test")
        await entity_repository.add(entity)
        # when
        result = await entity_repository.update(entity.change_field("changed"))
        # then
        assert result.field == "changed"

    async def test_async_update_all_should_update_all_entities(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity1 = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        entity2 = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        await audited_entity_repository.add_all([entity1, entity2])
        # when
        result1, result2 = await audited_entity_repository.update_all(
            [
                entity1.change_field("changed 1"),
                entity2.change_field("changed 2"),
            ]
        )
        # then
        assert result1.field == "changed 1"
        assert result2.field == "changed 2"

    async def test_async_delete_should_delete_entity(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        await audited_entity_repository.add(entity)
        # when
        result = await audited_entity_repository.delete(entity)
        # then
        assert result is True
