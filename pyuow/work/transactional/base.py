import abc
import typing as t
from abc import ABC

from ...result import OUT, Result
from ...units import CONTEXT, BaseUnit
from ..base import BaseWorkManager, BaseWorkProxy

TRANSACTION_PROVIDER = t.TypeVar("TRANSACTION_PROVIDER")


class BaseTransaction(t.Generic[TRANSACTION_PROVIDER], ABC):
    @abc.abstractmethod
    def it(self) -> TRANSACTION_PROVIDER:
        ...

    @abc.abstractmethod
    async def rollback(self) -> None:
        ...

    @abc.abstractmethod
    async def commit(self) -> None:
        ...


TRANSACTION = t.TypeVar("TRANSACTION", bound=BaseTransaction[t.Any])


class BaseTransactionManager(t.Generic[TRANSACTION], ABC):
    @abc.abstractmethod
    def transaction(self) -> t.AsyncContextManager[TRANSACTION]:
        ...


class TransactionalWorkProxy(BaseWorkProxy):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
        unit: BaseUnit[CONTEXT, OUT],
    ) -> None:
        self._transaction_manager = transaction_manager
        self._unit = unit

    async def do_with(self, context: t.Any, **kwargs: t.Any) -> Result[t.Any]:
        async with self._transaction_manager.transaction() as trx:
            result = await self._unit(context, **kwargs)

            if result.is_error():
                await trx.rollback()
            else:
                await trx.commit()

            return result


class TransactionalWorkManager(BaseWorkManager):
    def __init__(
        self,
        *,
        transaction_manager: BaseTransactionManager[TRANSACTION],
    ) -> None:
        self._transaction_manager = transaction_manager

    def by(self, unit: BaseUnit[CONTEXT, OUT]) -> BaseWorkProxy:
        return TransactionalWorkProxy(
            transaction_manager=self._transaction_manager,
            unit=unit,
        )
