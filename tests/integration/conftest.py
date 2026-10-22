"""Integration tests run against a real Postgres with pgvector.

Set ``TEST_DATABASE_URL`` to an empty database you do not mind wiping, for example
``postgresql://postgres:postgres@localhost:5432/rag_test``. Without it these tests are skipped.
"""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.integration


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            if not TEST_DATABASE_URL:
                item.add_marker(pytest.mark.skip(reason="TEST_DATABASE_URL is not set"))


@pytest.fixture(scope="session")
def database_url() -> str:
    assert TEST_DATABASE_URL
    return Settings(database_url=TEST_DATABASE_URL).database_url


@pytest.fixture(scope="session")
def alembic_config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.attributes["database_url"] = database_url
    return config


@pytest.fixture(scope="session")
def engine(database_url: str, alembic_config: Config) -> Iterator[Engine]:
    engine = create_engine(database_url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
        conn.execute(text("DROP TYPE IF EXISTS doc_status, job_status CASCADE"))
    command.upgrade(alembic_config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE documents, queries, jobs RESTART IDENTITY CASCADE"))
