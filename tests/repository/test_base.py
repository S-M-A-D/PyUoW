import typing as t
from dataclasses import dataclass
from unittest.mock import Mock
from uuid import UUID

import pytest

from pyuow.entity import Entity
from pyuow.entity.base import ENTITY_ID
from pyuow.repository import BaseEntityRepository, BaseRepositoryFactory


@dataclass(frozen=True)
class FakeEntity(Entity[UUID]):
    pass


class FakeBaseEntityRepository(BaseEntityRepository[UUID, FakeEntity]):

    def find(self, entity_id: UUID) -> t.Optional[FakeEntity]:
        return None

    def find_all(self, entity_ids: t.Iterable[UUID]) -> t.Iterable[FakeEntity]:
        return []

    def get(self, entity_id: UUID) -> FakeEntity:
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

    def exists(self, entity_id: ENTITY_ID) -> bool:
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
