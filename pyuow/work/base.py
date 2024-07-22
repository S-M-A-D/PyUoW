import abc
from abc import ABC

from ..result import OUT, Result
from ..units import CONTEXT, BaseAsyncUnit, BaseUnit


class BaseUnitProxy(BaseUnit[CONTEXT, OUT], ABC):
    def do_with(self, context: CONTEXT) -> Result[OUT]:
        return self(context)


class BaseAsyncUnitProxy(BaseAsyncUnit[CONTEXT, OUT], ABC):
    async def do_with(self, context: CONTEXT) -> Result[OUT]:
        return await self(context)


class BaseWorkManager(ABC):
    @abc.abstractmethod
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseUnitProxy[CONTEXT, OUT]:
        raise NotImplementedError


class BaseAsyncWorkManager(ABC):
    @abc.abstractmethod
    def by(
        self, unit: BaseAsyncUnit[CONTEXT, OUT]
    ) -> BaseAsyncUnitProxy[CONTEXT, OUT]:
        raise NotImplementedError
