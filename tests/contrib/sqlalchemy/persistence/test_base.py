from __future__ import annotations

import typing as t
from dataclasses import dataclass, replace
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import Mapped

from pyuow.contrib.sqlalchemy.persistence import AuditedEntityTable
from pyuow.contrib.sqlalchemy.persistence.repository import (
    BaseSqlAlchemyEntityRepository,
    BaseSqlAlchemyRepositoryFactory,
)
from pyuow.contrib.sqlalchemy.work import (
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)
from pyuow.persistence import AuditedEntity, Entity
from pyuow.persistence.repository import BaseEntityRepository

TestingEntityId = t.NewType("TestingEntityId", UUID)


@dataclass(frozen=True, kw_only=True)
class FakeAuditedEntity(AuditedEntity[TestingEntityId]):
    field: str

    def change_field(self, value: str) -> FakeAuditedEntity:
        return replace(self, field=value)


class FakeEntityTable(AuditedEntityTable):
    __tablename__ = "fake_entities"

    field: Mapped[str]


class FakeEntityRepository(
    BaseSqlAlchemyEntityRepository[
        TestingEntityId, FakeAuditedEntity, FakeEntityTable
    ]
):
    @staticmethod
    def to_entity(record: FakeEntityTable) -> FakeAuditedEntity:
        return FakeAuditedEntity(
            id=record.id,
            field=record.field,
            created_date=record.created_date,
            updated_date=record.updated_date,
        )

    @staticmethod
    def to_record(entity: FakeAuditedEntity) -> FakeEntityTable:
        return FakeEntityTable(
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
            FakeAuditedEntity: FakeEntityRepository(
                FakeEntityTable,
                self._transaction_manager,
                self._readonly_transaction_manager,
            ),
        }


@pytest.fixture
def repository_factory(engine: AsyncEngine) -> FakeRepositoryFactory:
    return FakeRepositoryFactory(
        transaction_manager=SqlAlchemyTransactionManager(engine),
        readonly_transaction_manager=SqlAlchemyReadOnlyTransactionManager(
            engine
        ),
    )


class TestSqlAlchemyEntityRepository:
    @pytest.fixture
    def repository(
        self, repository_factory: FakeRepositoryFactory
    ) -> BaseEntityRepository:
        return repository_factory.repo_for(FakeAuditedEntity)

    async def test_find_should_find_entity(
        self, repository: FakeEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        await repository.add(entity)
        # when
        result = await repository.find(entity.id)
        # then
        assert result == entity

    async def test_find_all_should_find_all_entities(
        self, repository: FakeEntityRepository
    ) -> None:
        # given
        entity1 = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        entity2 = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        await repository.add_all([entity1, entity2])
        # when
        result = await repository.find_all([entity1.id, entity2.id])
        # then
        assert {e for e in result} == {entity1, entity2}

    async def test_get_should_get_existing_entity(
        self, repository: FakeEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        await repository.add(entity)
        # when
        result = await repository.get(entity.id)
        # then
        assert result == entity

    async def test_get_should_raise_if_no_entity_found(
        self, repository: FakeEntityRepository
    ) -> None:
        # given
        entity_id = TestingEntityId(uuid4())
        # when / then
        with pytest.raises(NoResultFound):
            await repository.get(entity_id)

    async def test_exists_should_return_true_if_entity_exists(
        self, repository: FakeEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        await repository.add(entity)
        # when
        result = await repository.exists(entity.id)
        # then
        assert result is True

    async def test_exists_should_return_false_if_no_entity_found(
        self, repository: FakeEntityRepository
    ) -> None:
        # given
        entity_id = TestingEntityId(uuid4())
        # when
        result = await repository.exists(entity_id)
        # then
        assert result is False

    async def test_update_should_update_entity(
        self, repository: FakeEntityRepository
    ):
        # given
        entity = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        await repository.add(entity)
        # when
        result = await repository.update(entity.change_field("changed"))
        # then
        assert result.field == "changed"
        assert result.updated_date > entity.updated_date

    async def test_update_all_should_update_all_entities(
        self, repository: FakeEntityRepository
    ):
        # given
        entity1 = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        entity2 = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        await repository.add_all([entity1, entity2])
        # when
        result1, result2 = await repository.update_all(
            [
                entity1.change_field("changed 1"),
                entity2.change_field("changed 2"),
            ]
        )
        # then
        assert result1.field == "changed 1"
        assert result2.field == "changed 2"

    async def test_delete_should_delete_entity(
        self, repository: FakeEntityRepository
    ):
        # given
        entity = FakeAuditedEntity(id=TestingEntityId(uuid4()), field="test")
        await repository.add(entity)
        # when
        result = await repository.delete(entity)
        # then
        assert result is True
