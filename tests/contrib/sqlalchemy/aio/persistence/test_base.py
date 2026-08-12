from __future__ import annotations

import typing as t
from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine

from pyuow.clock import offset_naive_utcnow
from pyuow.contrib.sqlalchemy.aio.repository import (
    BaseSqlAlchemyEntityRepository,
    BaseSqlAlchemyRepositoryFactory,
    BaseSqlAlchemyViewRepository,
    BaseSqlAlchemyViewRepositoryFactory,
)
from pyuow.contrib.sqlalchemy.aio.work import (
    SqlAlchemyReadOnlyTransactionManager,
    SqlAlchemyTransactionManager,
)
from pyuow.entity import Entity, Version
from pyuow.repository.aio import BaseEntityRepository, BaseViewRepository
from tests.fake_entities import (
    FakeAuditedEntity,
    FakeEntity,
    FakeEntityId,
    FakeVersionedEntity,
)
from tests.fake_views import FakeEntityView

from ...fake_tables import (
    FakeAuditedEntityTable,
    FakeEntityTable,
    FakeEntityViewTable,
    FakeVersionedEntityTable,
)


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
            deleted_date=record.deleted_date,
        )

    @staticmethod
    def to_record(entity: FakeAuditedEntity) -> FakeAuditedEntityTable:
        return FakeAuditedEntityTable(
            id=entity.id,
            field=entity.field,
            created_date=entity.created_date,
            updated_date=entity.updated_date,
            deleted_date=entity.deleted_date,
        )


class FakeVersionedEntityRepository(
    BaseSqlAlchemyEntityRepository[
        FakeEntityId, FakeVersionedEntity, FakeVersionedEntityTable
    ]
):
    @staticmethod
    def to_entity(record: FakeVersionedEntityTable) -> FakeVersionedEntity:
        return FakeVersionedEntity(
            id=FakeEntityId(record.id),
            field=record.field,
            version=Version(record.version),
        )

    @staticmethod
    def to_record(entity: FakeVersionedEntity) -> FakeVersionedEntityTable:
        return FakeVersionedEntityTable(
            id=entity.id,
            field=entity.field,
            version=entity.version,
        )


class FakeEntityViewRepository(
    BaseSqlAlchemyViewRepository[FakeEntityView, FakeEntityViewTable]
):
    @staticmethod
    def to_view(record: FakeEntityViewTable) -> FakeEntityView:
        return FakeEntityView(
            id=FakeEntityId(record.id),
            field=record.field,
            upper_field=record.upper_field,
        )

    async def find_by_field(self, field: str) -> t.Optional[FakeEntityView]:
        return await self.find_by(
            self.select().where(self._table.field == field)
        )

    async def find_all_by_field(
        self, field: str
    ) -> t.Iterable[FakeEntityView]:
        return await self.find_all_by(
            self.select().where(self._table.field == field)
        )

    async def get_by_field(self, field: str) -> FakeEntityView:
        return await self.get_by(
            self.select().where(self._table.field == field)
        )

    async def exists_by_field(self, field: str) -> bool:
        return await self.exists_by(
            self.select().where(self._table.field == field)
        )


class FakeRepositoryFactory(
    BaseSqlAlchemyRepositoryFactory, BaseSqlAlchemyViewRepositoryFactory
):
    @property
    def repositories(
        self,
    ) -> t.Mapping[
        t.Type[Entity[t.Any]],
        BaseEntityRepository[t.Any, t.Any],
    ]:
        return {
            FakeVersionedEntity: FakeVersionedEntityRepository(
                FakeVersionedEntityTable,
                self._transaction_manager,
                self._readonly_transaction_manager,
            ),
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

    @property
    def views(
        self,
    ) -> t.Mapping[
        t.Type[t.Any],
        BaseViewRepository[t.Any, t.Any],
    ]:
        return {
            FakeEntityView: FakeEntityViewRepository(
                FakeEntityViewTable,
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
    def versioned_entity_repository(
        self, repository_factory: FakeRepositoryFactory
    ) -> BaseEntityRepository[FakeEntityId, FakeVersionedEntity]:
        return repository_factory.repo_for(FakeVersionedEntity)

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

    async def test_find_should_return_none_when_entity_is_deleted(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(
            id=FakeEntityId(uuid4()),
            field="test",
            deleted_date=offset_naive_utcnow(),
        )
        await audited_entity_repository.add(entity)
        # when
        result = await audited_entity_repository.find(entity.id)
        # then
        assert result is None

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

    async def test_find_all_should_return_empty_sequence_when_entity_is_deleted(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity1 = FakeAuditedEntity(
            id=FakeEntityId(uuid4()),
            field="test",
            deleted_date=offset_naive_utcnow(),
        )
        entity2 = FakeAuditedEntity(
            id=FakeEntityId(uuid4()),
            field="test",
            deleted_date=offset_naive_utcnow(),
        )
        await audited_entity_repository.add_all([entity1, entity2])
        # when
        result = await audited_entity_repository.find_all(
            [entity1.id, entity2.id]
        )
        # then
        assert result == []

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

    async def test_get_should_raise_if_entity_deleted(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(
            id=FakeEntityId(uuid4()),
            field="test",
            deleted_date=offset_naive_utcnow(),
        )
        await audited_entity_repository.add(entity)
        # when / then
        with pytest.raises(NoResultFound):
            await audited_entity_repository.get(entity.id)

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

    async def test_exists_should_return_false_if_entity_deleted(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(
            id=FakeEntityId(uuid4()),
            field="test",
            deleted_date=offset_naive_utcnow(),
        )
        await audited_entity_repository.add(entity)
        # when
        result = await audited_entity_repository.exists(entity.id)
        # then
        assert result is False

    async def test_async_update_audited_entity_should_update_both_entity_and_date(
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

    async def test_update_audited_entity_should_raise_if_entity_deleted(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity = FakeAuditedEntity(
            id=FakeEntityId(uuid4()),
            field="test",
            deleted_date=offset_naive_utcnow(),
        )
        await audited_entity_repository.add(entity)
        # when / then
        with pytest.raises(NoResultFound):
            await audited_entity_repository.update(
                entity.change_field("changed")
            )

    async def test_async_update_versioned_entity_should_update_both_entity_and_version(
        self, versioned_entity_repository: FakeVersionedEntityRepository
    ) -> None:
        # given
        entity = FakeVersionedEntity(id=FakeEntityId(uuid4()), field="test")
        await versioned_entity_repository.add(entity)
        # when
        result = await versioned_entity_repository.update(
            entity.change_field("changed")
        )
        # then
        assert result.field == "changed"
        assert result.version == entity.version.next()

    async def test_async_update_versioned_entity_should_raise_if_no_entity_with_current_version_exists(
        self, versioned_entity_repository: FakeVersionedEntityRepository
    ) -> None:
        # given
        entity = FakeVersionedEntity(id=FakeEntityId(uuid4()), field="test")
        await versioned_entity_repository.add(entity)
        # when / then
        with pytest.raises(NoResultFound):
            await versioned_entity_repository.update(
                replace(entity, version=Version(123))
            )

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

    async def test_delete_all_should_delete_all_entities(
        self, audited_entity_repository: FakeAuditedEntityRepository
    ) -> None:
        # given
        entity1 = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        entity2 = FakeAuditedEntity(id=FakeEntityId(uuid4()), field="test")
        await audited_entity_repository.add_all([entity1, entity2])
        # when
        result = await audited_entity_repository.delete_all([entity1, entity2])
        # then
        assert result is True


@pytest.mark.skip_on_ci
class TestSqlAlchemyViewRepository:
    @pytest.fixture
    def entity_repository(
        self, repository_factory: FakeRepositoryFactory
    ) -> BaseEntityRepository[FakeEntityId, FakeEntity]:
        return repository_factory.repo_for(FakeEntity)

    @pytest.fixture
    def entity_view_repository(
        self, repository_factory: FakeRepositoryFactory
    ) -> BaseViewRepository[FakeEntityView, t.Any]:
        return repository_factory.view_for(FakeEntityView)

    async def test_async_find_by_should_find_view(
        self,
        entity_repository: FakeEntityRepository,
        entity_view_repository: FakeEntityViewRepository,
    ) -> None:
        # given
        entity = FakeEntity(id=FakeEntityId(uuid4()), field=str(uuid4()))
        await entity_repository.add(entity)
        # when
        result = await entity_view_repository.find_by_field(entity.field)
        # then
        assert result == FakeEntityView(
            id=entity.id,
            field=entity.field,
            upper_field=entity.field.upper(),
        )

    async def test_async_find_by_should_return_none_when_no_view_matches(
        self, entity_view_repository: FakeEntityViewRepository
    ) -> None:
        # when
        result = await entity_view_repository.find_by_field(str(uuid4()))
        # then
        assert result is None

    async def test_async_find_all_by_should_find_all_views(
        self,
        entity_repository: FakeEntityRepository,
        entity_view_repository: FakeEntityViewRepository,
    ) -> None:
        # given
        field = str(uuid4())
        entity1 = FakeEntity(id=FakeEntityId(uuid4()), field=field)
        entity2 = FakeEntity(id=FakeEntityId(uuid4()), field=field)
        await entity_repository.add_all([entity1, entity2])
        # when
        result = await entity_view_repository.find_all_by_field(field)
        # then
        assert {view.id for view in result} == {entity1.id, entity2.id}

    async def test_find_all_by_should_return_empty_sequence_when_no_view_matches(
        self, entity_view_repository: FakeEntityViewRepository
    ) -> None:
        # when
        result = await entity_view_repository.find_all_by_field(str(uuid4()))
        # then
        assert result == []

    async def test_async_get_by_should_get_existing_view(
        self,
        entity_repository: FakeEntityRepository,
        entity_view_repository: FakeEntityViewRepository,
    ) -> None:
        # given
        entity = FakeEntity(id=FakeEntityId(uuid4()), field=str(uuid4()))
        await entity_repository.add(entity)
        # when
        result = await entity_view_repository.get_by_field(entity.field)
        # then
        assert result.upper_field == entity.field.upper()

    async def test_async_get_by_should_raise_if_no_view_exists(
        self, entity_view_repository: FakeEntityViewRepository
    ) -> None:
        # when / then
        with pytest.raises(NoResultFound):
            await entity_view_repository.get_by_field(str(uuid4()))

    async def test_async_exists_by_should_return_true_if_view_exists(
        self,
        entity_repository: FakeEntityRepository,
        entity_view_repository: FakeEntityViewRepository,
    ) -> None:
        # given
        entity = FakeEntity(id=FakeEntityId(uuid4()), field=str(uuid4()))
        await entity_repository.add(entity)
        # when
        result = await entity_view_repository.exists_by_field(entity.field)
        # then
        assert result is True

    async def test_async_exists_by_should_return_false_if_no_view_found(
        self, entity_view_repository: FakeEntityViewRepository
    ) -> None:
        # when
        result = await entity_view_repository.exists_by_field(str(uuid4()))
        # then
        assert result is False
