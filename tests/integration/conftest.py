import asyncio
from asyncio import AbstractEventLoop
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import URL, create_engine
from sqlalchemy.ext.declarative import ConcreteBase
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.infra.database.base import Base
from app.main import Application
from settings.config import AppSettings, load_app_settings
from tests.utils import database


@pytest.fixture(scope="session")
def test_settings() -> AppSettings:
    return load_app_settings()


@pytest.fixture(scope="session", autouse=True)
async def event_loop() -> AsyncGenerator[AbstractEventLoop, None]:
    """Fixes error:
    ```ScopeMismatch: You tried to access the 'function' scoped fixture 'event_loop'
    with a 'session' scoped request object, involved factories```

    Also fixes error with unclosed loop in unit tests

    "https://github.com/pytest-dev/pytest-asyncio/issues/30#issuecomment-226947196"
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(scope="session")
def test_application(
    test_settings: AppSettings,
) -> Application:
    return Application(settings=test_settings)


@pytest.fixture(scope="session")
async def fastapi_app(
    test_application: Application,
) -> FastAPI:
    return test_application.fastapi_app


@pytest.fixture()
async def rest_client(
    fastapi_app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        app=fastapi_app,
        base_url="http://test",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest.fixture()
async def user_client(
    fastapi_app: FastAPI,
    test_settings: AppSettings,
) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        app=fastapi_app,
        base_url="http://test",
        headers={"Content-Type": "application/json", "USER-API-KEY": test_settings.USER_KEY_HEADER.get_secret_value()},
    ) as client:
        yield client


@pytest.fixture(autouse=True)
async def redis_client(fastapi_app: FastAPI) -> AsyncGenerator[Redis, None]:
    redis: Redis = await fastapi_app.state.container.adapters.redis_client()
    await redis.flushdb()
    yield redis
    await redis.flushdb()


@pytest.fixture(scope="session")
def sync_session(request: pytest.FixtureRequest, test_settings: AppSettings) -> scoped_session:
    return _sync_session(
        request=request,
        db_sync_dsn=test_settings.sync_db_url,
        db_schema_name=test_settings.POSTGRES_DB,
        db_host=test_settings.DB_HOST,
        db_base=Base,
        session=database.sync_session,
    )


def _sync_session(
    request: pytest.FixtureRequest,
    db_sync_dsn: URL,
    db_schema_name: str,
    db_host: str,
    db_base: ConcreteBase,
    session: scoped_session,
) -> scoped_session:
    """
    1. Создаем тестовую базу (CREATE DATABASE)
    2. Создаем Engine, в котором хранится connection pool для доступа к этой базе
    3. Создаем все таблицы, которые в базе должны храниться (множество таблиц берется из metadata объекта ConcreteBase)
    3. На всю pytest сессию создается 1 connection к базе.
    4. Прикрепляем созданную ранее 1 сессию алхимии (см tests/utils.py например) к коннекшну из пункта 3
    5. Прикрепляем созданную ранее 1 сессию алхимии к FactoryBoy -
       Теперь все фабрики FactoryBoy при создании будут использовать одну и ту же сессию в рамках одной базы
    6. После прогона каждого теста чистим все таблицы, которые изменили в рамках теста (см _clear_tables)
    7. После прогона всех тестов удаляем сессию и закрываем connection
    """
    if not db_sync_dsn.database.endswith("test"):
        message = "dsn for database `{db}` not ending on test. probably real db on host {host}".format(  # noqa: UP032
            db=db_schema_name,
            host=db_host,
        )
        pytest.exit(message)

    if database_exists(db_sync_dsn):
        logger.warning(
            "test database {db} already exists on host {host}, dropping it",
            db=db_schema_name,
            host=db_host,
        )
        drop_database(db_sync_dsn)

    create_database(db_sync_dsn)
    sync_engine = create_engine(
        db_sync_dsn,
        echo=False,
        isolation_level="READ COMMITTED",
    )
    db_base.metadata.create_all(sync_engine)

    connection = sync_engine.connect()
    # http://factoryboy.readthedocs.io/en/latest/orms.html#managing-sessions
    session.configure(bind=connection)

    def teardown() -> None:
        session.close()
        connection.close()
        logger.info(
            "dropping test database {db} host {host}: {db_name}",
            db=db_schema_name,
            host=db_host,
            db_name=db_base.__class__.__name__,
        )
        drop_database(db_sync_dsn)

    request.addfinalizer(teardown)

    return session


def _clear_tables(sync_session: Session, db_base: ConcreteBase) -> None:
    tables = reversed(db_base.metadata.sorted_tables)
    for table in tables:
        sync_session.execute(table.delete())
    sync_session.commit()

    # clears session identity map, so that it doesn't have deleted objects in memory
    sync_session.expunge_all()
    sync_session.expire_all()


def _sync_db(sync_session: Session, db_schema_name: str, db_host: str, db_base: ConcreteBase) -> Session:
    if not db_schema_name.endswith("test"):
        logger.error(
            "received dsn for database not ending on test - {db}, probably real db on host {host}, terminate tests",
            db=db_schema_name,
            host=db_host,
        )
        return
    try:
        yield sync_session
    finally:
        _clear_tables(sync_session, db_base)


@pytest.fixture()
def sync_db(sync_session: Session, test_settings: AppSettings) -> Session:
    yield from _sync_db(
        sync_session=sync_session,
        db_schema_name=test_settings.POSTGRES_DB,
        db_host=test_settings.DB_HOST,
        db_base=Base,
    )
