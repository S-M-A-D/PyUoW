import typing as t
from unittest.mock import Mock

import pytest

from pyuow.entity import Entity
from pyuow.repository import (
    BaseEntityRepository,
    BaseRepositoryFactory,
    BaseViewRepository,
    BaseViewRepositoryFactory,
)
from tests.fake_entities import FakeEntity, FakeEntityId
from tests.fake_views import FakeView


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


class FakeBaseViewRepository(BaseViewRepository[FakeView, str]):
    def find_by(self, criteria: str) -> t.Optional[FakeView]:
        return None

    def find_all_by(self, criteria: str) -> t.Iterable[FakeView]:
        return []

    def get_by(self, criteria: str) -> FakeView:
        return FakeView(field=criteria)

    def exists_by(self, criteria: str) -> bool:
        return True


class FakeViewRepositoryFactory(BaseViewRepositoryFactory):
    @property
    def views(
        self,
    ) -> t.Mapping[t.Type[t.Any], BaseViewRepository[t.Any, t.Any]]:
        return {FakeView: FakeBaseViewRepository()}


class TestViewRepositoryFactory:
    def test_view_for_should_return_proper_repository_for_view_type(
        self,
    ) -> None:
        # given
        factory = FakeViewRepositoryFactory()
        # then
        assert isinstance(factory.view_for(FakeView), FakeBaseViewRepository)

    def test_view_for_should_raise_if_no_repository_for_view_type(
        self,
    ) -> None:
        # given
        factory = FakeViewRepositoryFactory()
        # when / then
        with pytest.raises(KeyError):
            factory.view_for(Mock)
