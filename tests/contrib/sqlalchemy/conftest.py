from pathlib import Path
from typing import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine
from testcontainers.postgres import PostgresContainer

TEST_DB_SCHEMA = Path(__file__).parent / "test_db_schema.sql"


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def engine(postgres: PostgresContainer) -> Iterator[Engine]:
    engine = create_engine(
        postgres.get_connection_url(),
        echo=True,
        echo_pool=True,
        pool_pre_ping=True,
    )
    yield engine


@pytest.fixture(scope="session", autouse=True)
def migrated_db(engine: AsyncEngine) -> None:
    with engine.connect() as conn, conn.begin():
        sql_instructions = TEST_DB_SCHEMA.read_text(encoding="utf-8")
        statements = sql_instructions.split(";")
        for statement in statements:
            conn.execute(text(statement))
