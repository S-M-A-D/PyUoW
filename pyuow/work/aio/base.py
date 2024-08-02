import abc
from abc import ABC

from ...aio.unit import BaseUnit
from ...result import OUT, Result
from ...unit import CONTEXT


class BaseUnitProxy(BaseUnit[CONTEXT, OUT], ABC):
    async def do_with(self, context: CONTEXT) -> Result[OUT]:
        return await self(context)


class BaseWorkManager(ABC):
    @abc.abstractmethod
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseUnitProxy[CONTEXT, OUT]:
        raise NotImplementedError
