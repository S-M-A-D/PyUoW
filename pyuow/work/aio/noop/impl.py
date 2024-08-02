import typing as t

from ....context import BaseContext
from ....result import Result
from ....unit.aio import BaseUnit
from ...aio import BaseUnitProxy, BaseWorkManager

CONTEXT = t.TypeVar("CONTEXT", bound=BaseContext[t.Any])
OUT = t.TypeVar("OUT")


class NoOpUnitProxy(BaseUnitProxy[CONTEXT, OUT]):  # pragma: no cover
    def __init__(
        self,
        *,
        unit: BaseUnit[CONTEXT, OUT],
    ) -> None:
        self._unit = unit

    async def __call__(self, context: CONTEXT) -> Result[OUT]:
        return await self._unit(context)


class NoOpWorkManager(BaseWorkManager):  # pragma: no cover
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> NoOpUnitProxy[CONTEXT, OUT]:
        return NoOpUnitProxy(unit=unit)
