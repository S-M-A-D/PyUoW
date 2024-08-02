import abc
import typing as t
from abc import ABC

from ..context import BaseContext
from ..result import Result
from ..unit import BaseUnit

CONTEXT = t.TypeVar("CONTEXT", bound=BaseContext[t.Any])
OUT = t.TypeVar("OUT")


class BaseUnitProxy(BaseUnit[CONTEXT, OUT], ABC):
    def do_with(self, context: CONTEXT) -> Result[OUT]:
        return self(context)


class BaseWorkManager(ABC):
    @abc.abstractmethod
    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseUnitProxy[CONTEXT, OUT]:
        raise NotImplementedError
