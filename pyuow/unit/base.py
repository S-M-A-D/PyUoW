import abc
import typing as t
from abc import ABC

from ..context import BaseContext
from ..result import Result

CONTEXT = t.TypeVar("CONTEXT", bound=BaseContext[t.Any])
OUT = t.TypeVar("OUT")


class BaseUnit(t.Generic[CONTEXT, OUT], ABC):
    @abc.abstractmethod
    def __call__(self, context: CONTEXT) -> Result[OUT]:
        raise NotImplementedError
