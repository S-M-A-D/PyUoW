from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from pyuow.contrib.sqlalchemy.aio.work import (
    SqlAlchemyTransaction,
    SqlAlchemyTransactionManager,
)


@pytest.mark.skip_on_ci
class TestSqlAlchemyTransaction:
    async def test_async_rollback_should_call_nested_transaction_rollback(
        self,
    ) -> None:
        # given
        nested_trx = AsyncMock()
        trx_provider = Mock(
            in_nested_transaction=Mock(return_value=True),
            get_nested_transaction=Mock(return_value=nested_trx),
        )
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        await trx.rollback()
        # then
        nested_trx.rollback.assert_awaited_once()

    async def test_async_rollback_should_call_root_transaction_rollback(
        self,
    ) -> None:
        # given
        root_trx = AsyncMock()
        trx_provider = Mock(
            in_nested_transaction=Mock(return_value=False),
            in_transaction=Mock(return_value=True),
            get_transaction=Mock(return_value=root_trx),
        )
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        await trx.rollback()
        # then
        root_trx.rollback.assert_awaited_once()

    async def test_async_commit_should_call_nested_transaction_commit(
        self,
    ) -> None:
        # given
        nested_trx = AsyncMock()
        trx_provider = Mock(
            in_nested_transaction=Mock(return_value=True),
            get_nested_transaction=Mock(return_value=nested_trx),
        )
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        await trx.commit()
        # then
        nested_trx.commit.assert_awaited_once()

    async def test_async_commit_should_call_root_transaction_commit(
        self,
    ) -> None:
        # given
        root_trx = AsyncMock()
        trx_provider = Mock(
            in_nested_transaction=Mock(return_value=False),
            in_transaction=Mock(return_value=True),
            get_transaction=Mock(return_value=root_trx),
        )
        trx = SqlAlchemyTransaction(trx_provider)
        # when
        await trx.commit()
        # then
        root_trx.commit.assert_awaited_once()


@pytest.mark.skip_on_ci
class TestSqlAlchemyTransactionManager:
    async def test_async_transaction_should_return_same_session_if_called_in_already_opened_transaction(
        self, async_engine: AsyncEngine
    ) -> None:
        # given
        manager = SqlAlchemyTransactionManager(async_engine)
        # when
        async with manager.transaction() as trx:
            first_trx = trx.it().get_transaction()

            async with manager.transaction() as trx:
                second_trx = trx.it().get_transaction()
        # then
        assert first_trx == second_trx

    async def test_async_transaction_should_return_different_session_if_called_in_already_opened_transaction(
        self, async_engine: AsyncEngine
    ) -> None:
        # given
        manager = SqlAlchemyTransactionManager(async_engine)
        # when
        async with manager.transaction() as trx:
            first_trx = trx.it().get_transaction()

        async with manager.transaction() as trx:
            second_trx = trx.it().get_transaction()
        # then
        assert first_trx != second_trx
