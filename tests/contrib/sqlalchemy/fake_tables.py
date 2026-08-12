from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from pyuow.contrib.sqlalchemy.tables import (
    AuditedEntityTable,
    EntityTable,
    SoftDeletableEntityTable,
    VersionedEntityTable,
    ViewTable,
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


class FakeEntityViewTable(ViewTable):
    __tablename__ = "fake_entities_view"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    field: Mapped[str]
    upper_field: Mapped[str]
