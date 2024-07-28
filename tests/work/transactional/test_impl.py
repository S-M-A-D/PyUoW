import typing as t
from contextlib import contextmanager
from dataclasses import dataclass
from unittest.mock import Mock

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
    def __call__(
        self, context: FakeContext, **kwargs: t.Any
    ) -> Result[FakeOut]:
        return Result.ok(FakeOut())


class FailureUnit(BaseUnit[FakeContext, FakeOut]):
    def __call__(
        self, context: FakeContext, **kwargs: t.Any
    ) -> Result[FakeOut]:
        return Result.error(Exception("Something went wrong"))


class FakeTransaction(BaseTransaction[Mock]):
    def rollback(self) -> None:
        self._transaction_provider.rollback()

    def commit(self) -> None:
        self._transaction_provider.commit()


class FakeTransactionManager(BaseTransactionManager[FakeTransaction]):
    def __init__(self, trx_provider_factory: t.Callable[[], Mock]):
        self._trx_provider_factory = trx_provider_factory

    @contextmanager
    def transaction(self) -> t.Iterator[FakeTransaction]:
        yield FakeTransaction(self._trx_provider_factory())


class TestTransactionalUnitProxy:
    def test_do_with_should_commit_on_success(self):
        # given
        unit = SuccessUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = Mock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work_proxy = TransactionalUnitProxy(
            transaction_manager=transaction_manager, unit=unit
        )
        # when
        result = work_proxy.do_with(context=context)
        # then
        assert result.is_ok()
        transaction.commit.assert_called_once()

    def test_do_with_should_rollback_on_error(self):
        # given
        unit = FailureUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = Mock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work_proxy = TransactionalUnitProxy(
            transaction_manager=transaction_manager, unit=unit
        )
        # when
        result = work_proxy.do_with(context=context)
        # then
        assert result.is_error()
        transaction.rollback.assert_called_once()


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

    def test_example_fake_flow_should_pass(self):
        # given
        unit = SuccessUnit()
        params = FakeParams()
        context = FakeContext(params=params)
        transaction = Mock()
        transaction_manager = FakeTransactionManager(lambda: transaction)
        work = TransactionalWorkManager(
            transaction_manager=transaction_manager
        )
        # when
        result = work.by(unit).do_with(context)
        # then
        assert result.is_ok()
        assert result.get() == FakeOut()
