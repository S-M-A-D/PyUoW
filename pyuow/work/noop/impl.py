from ... import BaseAsyncUnit, BaseUnit
from ...result import OUT, Result
from ...units import CONTEXT
from ..base import (
    BaseAsyncUnitProxy,
    BaseAsyncWorkManager,
    BaseUnitProxy,
    BaseWorkManager,
)


class NoOpUnitProxy(BaseUnitProxy[CONTEXT, OUT]):  # pragma: no cover
    def __init__(
        self,
        *,
        unit: BaseUnit[CONTEXT, OUT],
    ) -> None:
        self._unit = unit

    def __call__(self, context: CONTEXT) -> Result[OUT]:
        return self._unit(context)


class NoOpAsyncUnitProxy(BaseAsyncUnitProxy[CONTEXT, OUT]):  # pragma: no cover
    def __init__(
        self,
        *,
        unit: BaseAsyncUnit[CONTEXT, OUT],
    ) -> None:
        self._unit = unit

    async def __call__(self, context: CONTEXT) -> Result[OUT]:
        return await self._unit(context)


class NoOpWorkManager(BaseWorkManager):  # pragma: no cover
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseUnitProxy[CONTEXT, OUT]:
        return NoOpUnitProxy(unit=unit)


class NoOpAsyncWorkManager(BaseAsyncWorkManager):  # pragma: no cover
    def by(
        self, unit: BaseAsyncUnit[CONTEXT, OUT]
    ) -> BaseAsyncUnitProxy[CONTEXT, OUT]:
        return NoOpAsyncUnitProxy(unit=unit)
