import abc
import typing as t
from abc import ABC

from ..result import Result
from ..units import CONTEXT, OUT, BaseUnit


class BaseWorkProxy(ABC):
    @abc.abstractmethod
    async def do_with(
        self,
        context: CONTEXT,
        **kwargs: t.Any,
    ) -> Result[OUT]:
        raise NotImplementedError


class BaseWorkManager(ABC):
    @abc.abstractmethod
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseWorkProxy:
        raise NotImplementedError
