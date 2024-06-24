from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)


class BaseTable(MappedAsDataclass, DeclarativeBase, kw_only=True):
    __abstract__ = True
    type_annotation_map = {
        UUID: postgresql.UUID(as_uuid=True),
    }


class EntityTable(BaseTable):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(primary_key=True)


class AuditedEntityTable(EntityTable):
    __abstract__ = True
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
