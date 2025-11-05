import typing as t
from asyncio import current_task
from contextlib import asynccontextmanager

try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        AsyncSessionTransaction,
        async_scoped_session,
        async_sessionmaker,
    )
except ImportError:  # pragma: no cover
    raise ImportError(
        "Seems that you are trying to import extra module that was not installed,"
        " please install pyuow[sqlalchemy]"
    )

from .....work.aio.transactional import BaseTransaction, BaseTransactionManager


class SqlAlchemyTransaction(BaseTransaction[AsyncSession]):
    async def _get_active_transaction(
        self,
    ) -> t.Union[AsyncSessionTransaction, None]:
        if self._transaction_provider.in_nested_transaction():
            return self._transaction_provider.get_nested_transaction()
        if self._transaction_provider.in_transaction():
            return self._transaction_provider.get_transaction()

        return None

    async def rollback(self) -> None:
        if trx := await self._get_active_transaction():
            await trx.rollback()

    async def commit(self) -> None:
        if trx := await self._get_active_transaction():
            await trx.commit()


class SqlAlchemyTransactionManager(
    BaseTransactionManager[SqlAlchemyTransaction]
):
    def __init__(self, engine: AsyncEngine) -> None:
        self._session_factory = async_scoped_session(
            async_sessionmaker(engine, expire_on_commit=False),
            scopefunc=current_task,
        )

    @asynccontextmanager
    async def transaction(self) -> t.AsyncIterator[SqlAlchemyTransaction]:
        session = self._session_factory()
        if session.in_transaction():
            async with session.begin_nested():
                yield SqlAlchemyTransaction(session)
        else:
            async with session.begin():
                yield SqlAlchemyTransaction(session)


class SqlAlchemyReadOnlyTransactionManager(SqlAlchemyTransactionManager):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(
            engine.execution_options(isolation_level="AUTOCOMMIT")
        )

    @asynccontextmanager
    async def transaction(self) -> t.AsyncIterator[SqlAlchemyTransaction]:
        async with self._session_factory() as session:
            yield SqlAlchemyTransaction(session)
