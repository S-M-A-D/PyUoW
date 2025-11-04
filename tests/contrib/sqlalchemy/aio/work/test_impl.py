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
    async def test_async_transaction_should_open_nested_transaction_if_called_in_already_opened_transaction(
        self, async_engine: AsyncEngine
    ) -> None:
        # given
        manager = SqlAlchemyTransactionManager(async_engine)
        # when
        async with manager.transaction() as trx:
            first_session = trx.it()

            async with manager.transaction() as trx2:
                second_session = trx2.it()

                # then
                assert first_session.in_transaction()
                assert second_session.in_nested_transaction()

            assert first_session.in_transaction()
            assert not second_session.in_nested_transaction()

        assert not first_session.in_transaction()

    async def test_async_transaction_should_not_open_nested_transaction_if_called_in_new_transaction(
        self, async_engine: AsyncEngine
    ) -> None:
        # given
        manager = SqlAlchemyTransactionManager(async_engine)
        # when
        async with manager.transaction() as trx:
            session = trx.it()

            # then
            assert session.in_transaction()
            assert not session.in_nested_transaction()

        assert not session.in_transaction()
