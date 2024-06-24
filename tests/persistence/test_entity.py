from dataclasses import dataclass
from uuid import UUID, uuid4

from pyuow.persistence.entities import AuditedEntity


@dataclass(frozen=True)
class FakeAuditedEntity(AuditedEntity[UUID]):
    pass


class TestAuditedEntity:
    def test_post_init_should_properly_set_defaults_to_audited(self):
        # given
        entity_id = uuid4()
        # when
        entity = FakeAuditedEntity(id=entity_id)
        # then
        assert entity.id == entity_id
        assert entity.created_date == entity.updated_date
