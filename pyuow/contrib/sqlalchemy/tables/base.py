from datetime import datetime
from uuid import UUID

try:
    from sqlalchemy import UUID as SA_UUID
    from sqlalchemy import DateTime
    from sqlalchemy.orm import (
        DeclarativeBase,
        Mapped,
        MappedAsDataclass,
        mapped_column,
    )
except ImportError:  # pragma: no cover
    raise ImportError(
        "Seems that you are trying to import extra module that was not installed,"
        " please install pyuow[sqlalchemy]"
    )


class BaseTable(MappedAsDataclass, DeclarativeBase):
    __abstract__ = True
    type_annotation_map = {
        UUID: SA_UUID(as_uuid=True),
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
