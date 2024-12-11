import typing as t
from uuid import UUID

from sqlalchemy.orm import Mapped

from pyuow.contrib.sqlalchemy.tables import (
    AuditedEntityTable,
    EntityTable,
    VersionedEntityTable,
)


class FakeEntityTable(EntityTable):
    __tablename__ = "fake_entities"

    field: Mapped[str]


class FakeAuditedEntityTable(AuditedEntityTable):
    __tablename__ = "fake_audited_entities"

    field: Mapped[str]


class FakeVersionedEntityTable(VersionedEntityTable):
    __tablename__ = "fake_versioned_entities"

    field: Mapped[str]


FakeEntityId = t.NewType("FakeEntityId", UUID)
