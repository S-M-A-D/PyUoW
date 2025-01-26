import typing as t
from unittest.mock import Mock
from uuid import uuid4

import pytest

from pyuow.domain import Batch
from pyuow.entity import Entity
from pyuow.repository import (
    BaseDomainRepository,
    BaseEntityRepository,
    BaseRepositoryFactory,
)
from tests.fake_entities import FakeEntity, FakeEntityId, FakeModel


class FakeBaseEntityRepository(BaseEntityRepository[FakeEntityId, FakeEntity]):
    def find(self, entity_id: FakeEntityId) -> t.Optional[FakeEntity]:
        return None

    def find_all(
        self, entity_ids: t.Iterable[FakeEntityId]
    ) -> t.Iterable[FakeEntity]:
        return []

    def get(self, entity_id: FakeEntityId) -> FakeEntity:
        return FakeEntity(id=entity_id)

    def add(self, entity: FakeEntity) -> FakeEntity:
        return entity

    def add_all(
        self, entities: t.Sequence[FakeEntity]
    ) -> t.Iterable[FakeEntity]:
        return entities

    def update(self, entity: FakeEntity) -> FakeEntity:
        return entity

    def update_all(
        self, entities: t.Sequence[FakeEntity]
    ) -> t.Iterable[FakeEntity]:
        return entities

    def delete(self, entity: FakeEntity) -> bool:
        return True

    def delete_all(self, entities: t.Sequence[FakeEntity]) -> bool:
        return True

    def exists(self, entity_id: FakeEntityId) -> bool:
        return True


class FakeRepositoryFactory(BaseRepositoryFactory):
    @property
    def repositories(
        self,
    ) -> t.Mapping[t.Type[Entity[t.Any]], BaseEntityRepository[t.Any, t.Any]]:
        return {FakeEntity: FakeBaseEntityRepository()}


class TestRepositoryFactory:
    def test_repo_for_should_return_proper_repository_for_entity_type(
        self,
    ) -> None:
        # given
        factory = FakeRepositoryFactory()
        # then
        assert isinstance(
            factory.repo_for(FakeEntity), FakeBaseEntityRepository
        )

    def test_repo_for_should_raise_if_no_repository_for_entity_type(
        self,
    ) -> None:
        # given
        factory = FakeRepositoryFactory()
        # when / then
        with pytest.raises(KeyError):
            factory.repo_for(Mock)


class TestBaseDomainRepository:
    async def test_process_batch_should_properly_direct_changes_and_handle_events(
        self,
    ) -> None:
        # given
        add_mock = Mock()
        update_mock = Mock()
        delete_mock = Mock()
        factory_mock = Mock(
            repo_for=lambda *_, **__: Mock(
                add=add_mock, update=update_mock, delete=delete_mock
            )
        )
        events_handler_mock = Mock()
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
        repository.process_batch(batch)
        # then
        add_mock.assert_called_with(add_entity)
        update_mock.assert_called_with(update_entity)
        delete_mock.assert_called_with(delete_entity)
        events_handler_mock.assert_called_with(batch.events())
