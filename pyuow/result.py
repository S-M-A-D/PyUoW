import typing as t
from dataclasses import dataclass

from .exceptions import MissingOutError
from .types import MISSING, MissingType

OUT = t.TypeVar("OUT")


@dataclass(frozen=True, slots=True, repr=False)
@t.final
class Result(t.Generic[OUT]):
    _out: OUT | MissingType | Exception

    def get(self) -> OUT:
        match self._out:
            case MissingType():
                raise MissingOutError
            case Exception():
                raise self._out

        return self._out

    def or_raise(self) -> OUT:
        return self.get()

    def is_ok(self) -> bool:
        return not (self.is_error() or self.is_empty())

    def is_empty(self) -> bool:
        return isinstance(self._out, MissingType)

    def is_error(self) -> bool:
        return isinstance(self._out, Exception)

    @staticmethod
    def ok(out: OUT) -> "Result[OUT]":
        return Result(out)

    @staticmethod
    def error(exc: Exception) -> "Result[OUT]":
        return Result(exc)

    @staticmethod
    def empty() -> "Result[OUT]":
        return Result(MISSING)

    def __repr__(self) -> str:
        return self._out.__repr__()
