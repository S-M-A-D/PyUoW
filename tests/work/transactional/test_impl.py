import typing as t
from contextlib import asynccontextmanager
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

from pyuow import BaseContext, BaseUnit, Result
from pyuow.work.transactional import (
    BaseTransaction,
    BaseTransactionManager,
    TransactionalUnitProxy,
    TransactionalWorkManager,
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


class SuccessUnit(BaseUnit[FakeContext, FakeOut]):
    async def __call__(
        self, context: FakeContext, **kwargs: t.Any
    ) -> Result[FakeOut]:
        return Result.ok(FakeOut())


class FailureUnit(BaseUnit[FakeContext, FakeOut]):
    async def __call__(
        self, context: FakeContext, **kwargs: t.Any
    ) -> Result[FakeOut]:
        return Result.error(Exception("Something went wrong"))


class FakeTransaction(BaseTransaction[Mock]):
    def __init__(self, trx_provider: Mock):
        self._trx_provider = trx_provider

    def it(self) -> Mock:
        return self._trx_provider

    async def rollback(self) -> None:
        await self._trx_provider.rollback()

    async def commit(self) -> None:
        await self._trx_provider.commit()


class FakeTransactionManager(BaseTransactionManager[FakeTransaction]):
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
        work_proxy = TransactionalUnitProxy(
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
        work_proxy = TransactionalUnitProxy(
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
        transaction_manager = Mock(spec=BaseTransactionManager)
        work_manager = TransactionalWorkManager(
            transaction_manager=transaction_manager
        )
        unit = SuccessUnit()
        # when
        proxy = work_manager.by(unit)
        # then
        assert isinstance(proxy, TransactionalUnitProxy)

    async def test_example_fake_flow_should_pass(self):
        # given
        unit = SuccessUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = AsyncMock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work = TransactionalWorkManager(
            transaction_manager=transaction_manager
        )
        # when
        result = await work.by(unit).do_with(context)
        # then
        assert result.is_ok()
        assert result.get() == FakeOut()
