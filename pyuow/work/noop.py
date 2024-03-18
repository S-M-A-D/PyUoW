import typing as t

from .. import BaseUnit
from ..result import OUT, Result
from ..units import CONTEXT
from .base import BaseWorkManager, BaseWorkProxy


class NoOpWorkProxy(BaseWorkProxy):
    def __init__(
        self,
        *,
        unit: BaseUnit[CONTEXT, OUT],
    ) -> None:
        self._unit = unit

    async def do_with(self, context: t.Any, **kwargs: t.Any) -> Result[t.Any]:
        return await self._unit(context, **kwargs)


class NoOpWorkManager(BaseWorkManager):
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseWorkProxy:
        return NoOpWorkProxy(unit=unit)
