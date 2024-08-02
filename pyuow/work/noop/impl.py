import typing as t

from ...context import BaseContext
from ...result import Result
from ..base import BaseUnit, BaseUnitProxy, BaseWorkManager

CONTEXT = t.TypeVar("CONTEXT", bound=BaseContext[t.Any])
OUT = t.TypeVar("OUT")


class NoOpUnitProxy(BaseUnitProxy[CONTEXT, OUT]):  # pragma: no cover
    def __init__(
        self,
        *,
        unit: BaseUnit[CONTEXT, OUT],
    ) -> None:
        self._unit = unit

    def __call__(self, context: CONTEXT) -> Result[OUT]:
        return self._unit(context)


class NoOpWorkManager(BaseWorkManager):  # pragma: no cover
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseUnitProxy[CONTEXT, OUT]:
        return NoOpUnitProxy(unit=unit)
