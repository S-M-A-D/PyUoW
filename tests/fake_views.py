from __future__ import annotations

from dataclasses import dataclass

from tests.fake_entities import FakeEntityId


@dataclass(frozen=True)
class FakeView:
    field: str = "test"


@dataclass(frozen=True)
class FakeEntityView:
    id: FakeEntityId
    field: str
    upper_field: str
