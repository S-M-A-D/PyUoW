import typing as t
from dataclasses import dataclass
from uuid import UUID

from pyuow.persistence.entity import Entity
from pyuow.persistence.repository import (
    BaseEntityRepository,
    BaseRepositoryFactory,
)


@dataclass(frozen=True)
class FakeEntity(Entity[UUID]):
    pass


class FakeBaseEntityRepository(BaseEntityRepository[UUID, FakeEntity]):
    def get(self, entity_id: UUID) -> FakeEntity:
        pass

    def add(self, entity: FakeEntity) -> FakeEntity:
        pass

    def update(self, entity: FakeEntity) -> FakeEntity:
        pass

    def delete(self, entity: FakeEntity) -> bool:
        pass


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
