import os
from pathlib import Path
from typing import Self

from dependency_injector import containers
from dependency_injector.providers import Container, Singleton
from dependency_injector.wiring import Provide

from app.di.adapters import AdaptersContainer
from app.di.repositories import RepositoriesContainer
from app.di.services import ServicesContainer
from settings.config import AppSettings, load_app_settings, load_env

load_env()


class AsyncProvide(Provide):
    async def __call__(self) -> Self:
        return self


def _get_wiring_modules() -> set[str]:
    BASE_DIR = Path(__file__).parent.parent
    modules = set()

    for directory, _, files in os.walk(BASE_DIR):
        for file_name in files:
            relative_dir = os.path.relpath(directory, BASE_DIR)
            relative_file = ".".join([BASE_DIR.name, relative_dir.replace("/", "."), file_name.replace(".py", "")])
            if ("deps" in relative_file or "controllers" in relative_file) and "__" not in relative_file:
                modules.add(relative_file)
    return modules


class DIContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=_get_wiring_modules())

    settings: Singleton[AppSettings] = Singleton(load_app_settings)

    adapters: Container[AdaptersContainer] = Container(AdaptersContainer, settings=settings)
    repositories: Container[RepositoriesContainer] = Container(
        RepositoriesContainer, settings=settings, adapters=adapters
    )
    services: Container[ServicesContainer] = Container(
        ServicesContainer, settings=settings, repositories=repositories, adapters=adapters
    )
