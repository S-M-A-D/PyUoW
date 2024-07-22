import typing as t
from contextlib import asynccontextmanager
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

from pyuow import BaseAsyncUnit, BaseContext, Result
from pyuow.work.transactional import (
    BaseAsyncTransaction,
    BaseAsyncTransactionManager,
    TransactionalAsyncUnitProxy,
    TransactionalAsyncWorkManager,
)


@dataclass
class FakeParams:
    pass


@dataclass
class FakeContext(BaseContext[FakeParams]):
    pass


@dataclass(frozen=True)
class FakeOut:
    pass


class SuccessUnit(BaseAsyncUnit[FakeContext, FakeOut]):
    async def __call__(
        self, context: FakeContext, **kwargs: t.Any
    ) -> Result[FakeOut]:
        return Result.ok(FakeOut())


class FailureUnit(BaseAsyncUnit[FakeContext, FakeOut]):
    async def __call__(
        self, context: FakeContext, **kwargs: t.Any
    ) -> Result[FakeOut]:
        return Result.error(Exception("Something went wrong"))


class FakeTransaction(BaseAsyncTransaction[Mock]):
    async def rollback(self) -> None:
        await self._transaction_provider.rollback()

    async def commit(self) -> None:
        await self._transaction_provider.commit()


class FakeTransactionManager(BaseAsyncTransactionManager[FakeTransaction]):
    def __init__(self, trx_provider_factory: t.Callable[[], Mock]):
        self._trx_provider_factory = trx_provider_factory

    @asynccontextmanager
    async def transaction(self) -> t.AsyncIterator[FakeTransaction]:
        yield FakeTransaction(self._trx_provider_factory())


class TestTransactionalUnitProxy:
    async def test_do_with_should_commit_on_success(self):
        # given
        unit = SuccessUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = AsyncMock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work_proxy = TransactionalAsyncUnitProxy(
            transaction_manager=transaction_manager, unit=unit
        )
        # when
        result = await work_proxy.do_with(context=context)
        # then
        assert result.is_ok()
        transaction.commit.assert_awaited_once()

    async def test_do_with_should_rollback_on_error(self):
        # given
        unit = FailureUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = AsyncMock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work_proxy = TransactionalAsyncUnitProxy(
            transaction_manager=transaction_manager, unit=unit
        )
        # when
        result = await work_proxy.do_with(context=context)
        # then
        assert result.is_error()
        transaction.rollback.assert_awaited_once()


class TestTransactionalWorkManager:
    def test_by_should_delegate_unit_to_work_proxy(self):
        # given
        transaction_manager = Mock(spec=BaseAsyncTransactionManager)
        work_manager = TransactionalAsyncWorkManager(
            transaction_manager=transaction_manager
        )
        unit = SuccessUnit()
        # when
        proxy = work_manager.by(unit)
        # then
        assert isinstance(proxy, TransactionalAsyncUnitProxy)

    async def test_example_fake_flow_should_pass(self):
        # given
        unit = SuccessUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = AsyncMock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work = TransactionalAsyncWorkManager(
            transaction_manager=transaction_manager
        )
        # when
        result = await work.by(unit).do_with(context)
        # then
        assert result.is_ok()
        assert result.get() == FakeOut()
