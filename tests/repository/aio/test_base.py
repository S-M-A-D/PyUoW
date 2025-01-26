import typing as t
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from pyuow.domain import Batch
from pyuow.entity import Entity
from pyuow.repository.aio import BaseEntityRepository, BaseRepositoryFactory
from pyuow.repository.aio.base import BaseDomainRepository
from tests.fake_entities import FakeEntity, FakeEntityId, FakeModel


class FakeBaseEntityRepository(BaseEntityRepository[FakeEntityId, FakeEntity]):
    async def find(self, entity_id: FakeEntityId) -> t.Optional[FakeEntity]:
        return None

    async def find_all(
        self, entity_ids: t.Iterable[FakeEntityId]
    ) -> t.Iterable[FakeEntity]:
        return []

    async def get(self, entity_id: FakeEntityId) -> FakeEntity:
        return FakeEntity(id=entity_id)

    async def add(self, entity: FakeEntity) -> FakeEntity:
        return entity

    async def add_all(
        self, entities: t.Sequence[FakeEntity]
    ) -> t.Iterable[FakeEntity]:
        return entities

    async def update(self, entity: FakeEntity) -> FakeEntity:
        return entity

    async def update_all(
        self, entities: t.Sequence[FakeEntity]
    ) -> t.Iterable[FakeEntity]:
        return entities

    async def delete(self, entity: FakeEntity) -> bool:
        return True

    async def delete_all(self, entities: t.Sequence[FakeEntity]) -> bool:
        return True

    async def exists(self, entity_id: FakeEntityId) -> bool:
        return True


class FakeRepositoryFactory(BaseRepositoryFactory):
    @property
    def repositories(
        self,
    ) -> t.Mapping[t.Type[Entity[t.Any]], BaseEntityRepository[t.Any, t.Any]]:
        return {FakeEntity: FakeBaseEntityRepository()}


class TestRepositoryFactory:
    def test_async_repo_for_should_return_proper_repository_for_entity_type(
        self,
    ) -> None:
        # given
        factory = FakeRepositoryFactory()
        # then
        assert isinstance(
            factory.repo_for(FakeEntity), FakeBaseEntityRepository
        )

    def test_async_repo_for_should_raise_if_no_repository_for_entity_type(
        self,
    ) -> None:
        # given
        factory = FakeRepositoryFactory()
        # when
        with pytest.raises(KeyError):
            factory.repo_for(Mock)


class TestBaseDomainRepository:
    async def test_async_process_batch_should_properly_direct_changes_and_handle_events(
        self,
    ) -> None:
        # given
        add_mock = AsyncMock()
        update_mock = AsyncMock()
        delete_mock = AsyncMock()
        factory_mock = Mock(
            repo_for=lambda *_, **__: AsyncMock(
                add=add_mock, update=update_mock, delete=delete_mock
            )
        )
        events_handler_mock = AsyncMock()
        repository = BaseDomainRepository(
            repositories=factory_mock,
            events_handler=events_handler_mock,
        )

        add_entity = FakeModel()
        update_entity = FakeEntity(id=FakeEntityId(uuid4()))
        delete_entity = FakeEntity(id=FakeEntityId(uuid4()))

        batch = Batch()
        batch.add(add_entity)
        batch.update(update_entity)
        batch.delete(delete_entity)
        # when
        await repository.process_batch(batch)
        # then
        add_mock.assert_awaited_once_with(add_entity)
        update_mock.assert_awaited_once_with(update_entity)
        delete_mock.assert_awaited_once_with(delete_entity)
        events_handler_mock.assert_awaited_once_with(batch.events())
