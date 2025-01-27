from uuid import uuid4

import pytest

from pyuow.entity import Version
from tests.fake_entities import (
    FakeAuditedEntity,
    FakeEntityId,
    FakeVersionedEntity,
)


class TestAuditedEntity:
    def test_post_init_should_properly_set_defaults_to_audited(self) -> None:
        # given
        entity_id = FakeEntityId(uuid4())
        # when
        entity = FakeAuditedEntity(id=entity_id)
        # then
        assert entity.id == entity_id
        assert entity.created_date == entity.updated_date


class TestVersion:
    def test_init_should_raise_if_version_is_negative(self) -> None:
        # when / then
        with pytest.raises(ValueError, match="Version cannot be negative"):
            Version(-1)

    def test_next_should_properly_produce_next_version(self) -> None:
        # given
        version = Version(3)
        # when
        next_version = version.next()
        # when
        assert next_version == 4
        assert isinstance(next_version, Version)


class TestVersionedEntity:
    def test_init_should_properly_set_versions(self) -> None:
        # given
        entity_id = FakeEntityId(uuid4())
        # when
        entity = FakeVersionedEntity(id=entity_id)
        # then
        assert entity.id == entity_id
        assert entity.version == Version(0)
