import typing as t
from dataclasses import dataclass, field

from ...context import BaseContext
from ...domain import Batch
from ..base import BaseParams

PARAMS = t.TypeVar("PARAMS", bound=BaseParams)


@dataclass(frozen=True)
class BaseDomainContext(BaseContext[PARAMS]):
    params: PARAMS
    batch: Batch = field(default_factory=Batch)
