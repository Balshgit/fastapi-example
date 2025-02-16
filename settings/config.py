import os
from functools import cached_property, lru_cache

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL as DB_URL
from yarl import URL

from app.core.constants import LogLevelEnum, StageEnum


class BaseAppSettings(BaseSettings):
    STAGE: StageEnum
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.DEBUG
    ENABLE_JSON_LOGS: bool = True
    LOCALTEST: bool = False

    model_config = SettingsConfigDict(env_file="settings/environments/.env", extra="ignore")


class DataBaseSettings(BaseSettings):
    POSTGRES_DB_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    DB_ECHO: bool
    DB_HOST: str

    @cached_property
    def async_db_url(self) -> DB_URL:
        return DB_URL.create(
            drivername="postgresql+asyncpg",
            database=self.POSTGRES_DB,
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.DB_HOST,
            port=self.POSTGRES_DB_PORT,
        )

    @property
    def sync_db_url(self) -> DB_URL:
        return DB_URL.create(
            drivername="postgresql",
            database=self.POSTGRES_DB,
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.DB_HOST,
            port=self.POSTGRES_DB_PORT,
        )


class UsersSettings(BaseSettings):
    USER_KEY_HEADER: SecretStr


class RedisSettings(BaseSettings):
    REDIS_USER: str
    REDIS_PASSWORD: SecretStr
    REDIS_DATABASE: str | None
    REDIS_HOST: str
    REDIS_PORT: int

    @cached_property
    def redis_url(self) -> URL:
        """
        Assemble REDIS URL from settings.

        :return: redis URL.
        """
        path = f"/{self.REDIS_DATABASE}" if self.REDIS_DATABASE is not None else ""

        return URL.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            password=self.REDIS_PASSWORD.get_secret_value(),
            path=path,
        )


class AppSettings(BaseAppSettings, DataBaseSettings, UsersSettings, RedisSettings, BaseSettings):
    DEBUG: bool = False
    APP_HOST: str
    APP_PORT: int

    model_config = SettingsConfigDict(case_sensitive=True)


def load_env() -> None:
    is_local_test = BaseAppSettings().LOCALTEST or os.getenv("LOCALTEST", "False").lower() in ("true", "1", "t")  # type: ignore[call-arg]
    app_env = StageEnum.runtests if is_local_test else BaseAppSettings().STAGE  # type: ignore[call-arg]
    environment_path = "settings/environments/.env"
    if app_env is StageEnum.runtests and is_local_test:
        environment_path = "settings/environments/.env.local.runtests"
    load_dotenv(environment_path, override=is_local_test)


@lru_cache(maxsize=None)  # noqa: UP033
def load_app_settings() -> AppSettings:
    load_env()
    return AppSettings()  # type: ignore[call-arg]
