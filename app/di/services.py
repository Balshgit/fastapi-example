from dependency_injector import containers, providers
from dependency_injector.providers import Singleton

from app.core.users.services import UserService
from settings.config import AppSettings


class ServicesContainer(containers.DeclarativeContainer):
    settings: providers.Dependency[AppSettings] = providers.Dependency()

    repositories = providers.DependenciesContainer()
    adapters = providers.DependenciesContainer()

    user_service: Singleton[UserService] = Singleton(
        UserService,
        user_repository=repositories.user_repository,
        user_cache_repository=repositories.user_cache_repository,
    )
