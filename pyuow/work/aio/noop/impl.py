from ....aio import BaseUnit
from ....result import OUT, Result
from ....units import CONTEXT
from ...aio import BaseUnitProxy, BaseWorkManager


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
