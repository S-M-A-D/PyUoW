import abc
import typing as t
from abc import ABC

TRANSACTION_PROVIDER = t.TypeVar("TRANSACTION_PROVIDER")


class BaseTransaction(t.Generic[TRANSACTION_PROVIDER], ABC):
    @abc.abstractmethod
    def it(self) -> TRANSACTION_PROVIDER: ...

    @abc.abstractmethod
    async def rollback(self) -> None: ...

    @abc.abstractmethod
    async def commit(self) -> None: ...


TRANSACTION = t.TypeVar("TRANSACTION", bound=BaseTransaction[t.Any])


class BaseTransactionManager(t.Generic[TRANSACTION], ABC):
    @abc.abstractmethod
    def transaction(self) -> t.AsyncContextManager[TRANSACTION]: ...
