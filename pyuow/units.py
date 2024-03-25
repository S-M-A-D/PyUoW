import abc
import typing as t
from abc import ABC
from logging import getLogger

from .context import BaseContext
from .exceptions import CannotReassignUnitError, FinalUnitError
from .result import OUT, Result
from .types import MISSING, MissingType

logger = getLogger(__name__)

CONTEXT = t.TypeVar("CONTEXT", bound=BaseContext[t.Any])


class BaseUnit(t.Generic[CONTEXT, OUT], ABC):
    @abc.abstractmethod
    async def __call__(self, context: CONTEXT) -> Result[OUT]:
        raise NotImplementedError


class FlowUnit(BaseUnit[CONTEXT, OUT], ABC):
    def __init__(self) -> None:
        self._root: "FlowUnit[CONTEXT, OUT]" = self
        self._next: t.Union["FlowUnit[CONTEXT, OUT]", MissingType] = MISSING

    def __rshift__(
        self: "FlowUnit[CONTEXT, OUT]", other: "FlowUnit[CONTEXT, OUT]"
    ) -> "FlowUnit[CONTEXT, OUT]":
        if not isinstance(other._next, MissingType):
            raise CannotReassignUnitError

        self._next = other
        other._root = self._root
        return other

    def build(self) -> "FlowUnit[CONTEXT, OUT]":
        return self._root


class FinalUnit(FlowUnit[CONTEXT, OUT], ABC):
    async def __call__(self, context: CONTEXT) -> Result[OUT]:
        cls_name = self.__class__.__name__

        try:
            result = await self.finish(context)
        except Exception as error:
            logger.exception(
                "[%s] failed with exception", cls_name, exc_info=error
            )
            return Result.error(error)
        else:
            logger.info("[%s] completed", self.__class__.__name__)

        logger.debug("[%s] result [%s]", self.__class__.__name__, result)
        return result

    @abc.abstractmethod
    async def finish(self, context: CONTEXT) -> Result[OUT]:
        raise NotImplementedError

    def __rshift__(
        self: "FlowUnit[CONTEXT, OUT]", other: "FlowUnit[CONTEXT, OUT]"
    ) -> "FlowUnit[CONTEXT, OUT]":
        raise FinalUnitError(self.__class__.__name__)


@t.final
class ErrorUnit(FinalUnit[CONTEXT, OUT]):
    def __init__(
        self,
        exc: Exception,
    ) -> None:
        super().__init__()
        self._exc = exc

    async def finish(self, context: CONTEXT) -> Result[OUT]:
        return Result.error(self._exc)


class ConditionalUnit(FlowUnit[CONTEXT, OUT]):
    def __init__(self, *, on_failure: FlowUnit[CONTEXT, OUT]) -> None:
        super().__init__()
        self._on_failure = on_failure

    async def __call__(self, context: CONTEXT) -> Result[OUT]:
        cls_name = self.__class__.__name__

        if isinstance(self._next, MissingType):
            raise NotImplementedError(f"[{cls_name}] next unit is not set")

        try:
            passed = await self.condition(context)
        except Exception as error:
            logger.exception(
                "[%s] failed with exception", cls_name, exc_info=error
            )
            return Result.error(error)

        if passed:
            logger.info("[%s] completed", cls_name)
            return await self._next(context)

        logger.info("[%s] failed", cls_name)
        return await self._on_failure(context)

    @abc.abstractmethod
    async def condition(self, context: CONTEXT) -> bool:
        raise NotImplementedError


class RunUnit(FlowUnit[CONTEXT, OUT]):
    async def __call__(self, context: CONTEXT) -> Result[OUT]:
        cls_name = self.__class__.__name__

        if isinstance(self._next, MissingType):
            raise NotImplementedError(f"[{cls_name}] next unit is not set")

        try:
            await self.run(context)
        except Exception as error:
            logger.exception(
                "[%s] failed with exception", cls_name, exc_info=error
            )
            return Result.error(error)

        logger.info("[%s] completed", cls_name)
        return await self._next(context)

    @abc.abstractmethod
    async def run(self, context: CONTEXT) -> None:
        raise NotImplementedError
