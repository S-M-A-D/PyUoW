import abc
import typing as t
from abc import ABC

TRANSACTION_PROVIDER = t.TypeVar("TRANSACTION_PROVIDER")


class BaseTransaction(t.Generic[TRANSACTION_PROVIDER], ABC):
    def __init__(self, transaction_provider: TRANSACTION_PROVIDER) -> None:
        self._transaction_provider = transaction_provider

    def it(self) -> TRANSACTION_PROVIDER:
        return self._transaction_provider

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplementedError


class BaseAsyncTransaction(t.Generic[TRANSACTION_PROVIDER], ABC):
    def __init__(self, transaction_provider: TRANSACTION_PROVIDER) -> None:
        self._transaction_provider = transaction_provider

    def it(self) -> TRANSACTION_PROVIDER:
        return self._transaction_provider

    @abc.abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError


TRANSACTION = t.TypeVar("TRANSACTION", bound=BaseTransaction[t.Any])
ASYNC_TRANSACTION = t.TypeVar(
    "ASYNC_TRANSACTION", bound=BaseAsyncTransaction[t.Any]
)


class BaseTransactionManager(t.Generic[TRANSACTION], ABC):
    @abc.abstractmethod
    def transaction(self) -> t.ContextManager[TRANSACTION]:
        raise NotImplementedError


class BaseAsyncTransactionManager(t.Generic[ASYNC_TRANSACTION], ABC):
    @abc.abstractmethod
    def transaction(self) -> t.AsyncContextManager[ASYNC_TRANSACTION]:
        raise NotImplementedError
