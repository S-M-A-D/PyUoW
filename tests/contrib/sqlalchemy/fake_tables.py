from __future__ import annotations

from sqlalchemy.orm import Mapped

from pyuow.contrib.sqlalchemy.tables import (
    AuditedEntityTable,
    EntityTable,
    SoftDeletableEntityTable,
    VersionedEntityTable,
)


class FakeEntityTable(EntityTable):
    __tablename__ = "fake_entities"

    field: Mapped[str]


class FakeAuditedEntityTable(AuditedEntityTable, SoftDeletableEntityTable):
    __tablename__ = "fake_audited_entities"

    field: Mapped[str]


class FakeVersionedEntityTable(VersionedEntityTable):
    __tablename__ = "fake_versioned_entities"

    field: Mapped[str]
