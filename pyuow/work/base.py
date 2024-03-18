import abc
import typing as t
from abc import ABC

from ..result import Result
from ..units import CONTEXT, OUT, BaseUnit

WORK_MANAGER = t.TypeVar("WORK_MANAGER", bound="BaseWorkManager")


class BaseWorkProxy(ABC):
    @abc.abstractmethod
    async def do_with(
        self,
        context: CONTEXT,
        **kwargs: t.Any,
    ) -> Result[OUT]: ...


class BaseWorkManager(ABC):
    @abc.abstractmethod
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseWorkProxy: ...

    async def __aenter__(self: WORK_MANAGER) -> WORK_MANAGER:
        return self
