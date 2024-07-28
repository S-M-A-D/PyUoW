import typing as t
from asyncio import current_task
from contextlib import asynccontextmanager

try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
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
    async def rollback(self) -> None:
        await self._transaction_provider.rollback()

    async def commit(self) -> None:
        await self._transaction_provider.commit()


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
