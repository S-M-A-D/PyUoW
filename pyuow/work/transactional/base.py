import abc
import typing as t
from abc import ABC

TRANSACTION_PROVIDER = t.TypeVar("TRANSACTION_PROVIDER")
TRANSACTION = t.TypeVar("TRANSACTION", bound="BaseTransaction[t.Any]")


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


class BaseTransactionManager(t.Generic[TRANSACTION], ABC):
    @abc.abstractmethod
    def transaction(self) -> t.ContextManager[TRANSACTION]:
        raise NotImplementedError
