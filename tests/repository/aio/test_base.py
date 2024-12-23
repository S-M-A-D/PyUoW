import typing as t
from dataclasses import dataclass
from unittest.mock import Mock
from uuid import UUID

import pytest

from pyuow.entity import Entity
from pyuow.entity.base import ENTITY_ID
from pyuow.repository.aio import BaseEntityRepository, BaseRepositoryFactory


@dataclass(frozen=True)
class FakeEntity(Entity[UUID]):
    pass


class FakeBaseEntityRepository(BaseEntityRepository[UUID, FakeEntity]):
    async def find(self, entity_id: UUID) -> t.Optional[FakeEntity]:
        return None

    async def find_all(
        self, entity_ids: t.Iterable[UUID]
    ) -> t.Iterable[FakeEntity]:
        return []

    async def get(self, entity_id: UUID) -> FakeEntity:
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

    async def exists(self, entity_id: ENTITY_ID) -> bool:
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
