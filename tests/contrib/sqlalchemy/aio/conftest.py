from typing import Iterator
from pathlib import Path

import pytest
from sqlalchemy import NullPool, text
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.postgres import PostgresContainer


TEST_DB_SCHEMA = Path(__file__).parent.parent / "test_db_schema.sql"


@pytest.fixture(scope="session")
def async_postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:15", driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def async_engine(async_postgres: PostgresContainer) -> Iterator[AsyncEngine]:
    engine = create_async_engine(
        async_postgres.get_connection_url(),
        # NullPool is required for sqlalchemy in tests
        # to properly work with asyncio
        # https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-multiple-asyncio-event-loops
        poolclass=NullPool,
        echo=True,
        echo_pool=True,
        pool_pre_ping=True,
    )
    yield engine


@pytest.fixture(scope="session", autouse=True)
async def migrated_db(async_engine: AsyncEngine) -> None:
    async with async_engine.connect() as conn, conn.begin():
        sql_instructions = TEST_DB_SCHEMA.read_text(encoding="utf-8")
        statements = sql_instructions.split(";")
        for statement in statements:
            await conn.execute(text(statement))
