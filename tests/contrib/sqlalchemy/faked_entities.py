import typing as t
from uuid import UUID

from sqlalchemy.orm import Mapped

from pyuow.contrib.sqlalchemy.persistence.tables import (
    EntityTable,
    AuditedEntityTable,
)


class FakeEntityTable(EntityTable):
    __tablename__ = "fake_entities"

    field: Mapped[str]


class FakeAuditedEntityTable(AuditedEntityTable):
    __tablename__ = "fake_audited_entities"

    field: Mapped[str]


FakeEntityId = t.NewType("FakeEntityId", UUID)
