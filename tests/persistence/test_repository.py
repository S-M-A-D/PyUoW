import typing as t
from dataclasses import dataclass
from uuid import UUID

from pyuow.persistence.entity import ENTITY_ID
from pyuow.persistence.repository import (
    BaseEntityRepository,
    BaseRepositoryFactory,
    Entity,
)


@dataclass(frozen=True)
class FakeEntity(Entity[UUID]):
    pass


class FakeBaseEntityRepository(BaseEntityRepository[UUID, UUID]):
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

    def exists(self, entity_id: ENTITY_ID) -> bool:
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
    ):
        # given
        factory = FakeRepositoryFactory()
        # then
        assert isinstance(
            factory.repo_for(FakeEntity), FakeBaseEntityRepository
        )
