import typing as t
from asyncio import current_task
from contextlib import asynccontextmanager, contextmanager

try:
    from sqlalchemy import Engine
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_scoped_session,
        async_sessionmaker,
    )
    from sqlalchemy.orm import Session, scoped_session, sessionmaker
except ImportError:  # pragma: no cover
    raise ImportError(
        "Seems that you are trying to import extra module that was not installed,"
        " please install pyuow[sqlalchemy]"
    )

from ....work.transactional import (
    BaseAsyncTransaction,
    BaseAsyncTransactionManager,
    BaseTransaction,
    BaseTransactionManager,
)


class SqlAlchemyTransaction(BaseTransaction[Session]):
    def rollback(self) -> None:
        self._transaction_provider.rollback()

    def commit(self) -> None:
        self._transaction_provider.commit()


class SqlAlchemyAsyncTransaction(BaseAsyncTransaction[AsyncSession]):
    async def rollback(self) -> None:
        await self._transaction_provider.rollback()

    async def commit(self) -> None:
        await self._transaction_provider.commit()


class SqlAlchemyTransactionManager(
    BaseTransactionManager[SqlAlchemyTransaction]
):
    def __init__(self, engine: Engine) -> None:
        self._session_factory = scoped_session(
            sessionmaker(engine, expire_on_commit=False),
            scopefunc=current_task,
        )

    @contextmanager
    def transaction(self) -> t.Iterator[SqlAlchemyTransaction]:
        session = self._session_factory()
        if session.in_transaction():
            yield SqlAlchemyTransaction(session)
        else:
            with session.begin():
                yield SqlAlchemyTransaction(session)


class SqlAlchemyAsyncTransactionManager(
    BaseAsyncTransactionManager[SqlAlchemyAsyncTransaction]
):
    def __init__(self, engine: AsyncEngine) -> None:
        self._session_factory = async_scoped_session(
            async_sessionmaker(engine, expire_on_commit=False),
            scopefunc=current_task,
        )

    @asynccontextmanager
    async def transaction(self) -> t.AsyncIterator[SqlAlchemyAsyncTransaction]:
        session = self._session_factory()
        if session.in_transaction():
            yield SqlAlchemyAsyncTransaction(session)
        else:
            async with session.begin():
                yield SqlAlchemyAsyncTransaction(session)


class SqlAlchemyReadOnlyTransactionManager(SqlAlchemyTransactionManager):
    def __init__(self, engine: Engine) -> None:
        super().__init__(
            engine.execution_options(isolation_level="AUTOCOMMIT")
        )

    @contextmanager
    def transaction(self) -> t.Iterator[SqlAlchemyTransaction]:
        with self._session_factory() as session:
            yield SqlAlchemyTransaction(session)


class SqlAlchemyAsyncReadOnlyTransactionManager(
    SqlAlchemyAsyncTransactionManager
):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(
            engine.execution_options(isolation_level="AUTOCOMMIT")
        )

    @asynccontextmanager
    async def transaction(self) -> t.AsyncIterator[SqlAlchemyAsyncTransaction]:
        async with self._session_factory() as session:
            yield SqlAlchemyAsyncTransaction(session)
