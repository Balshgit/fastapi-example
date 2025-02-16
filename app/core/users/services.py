from dataclasses import dataclass

from app.core.users.dto import UpdateUserRequestDTO, UserDTO
from app.core.users.models import User
from app.core.users.repositories import UserCacheRepository, UserRepository


@dataclass
class UserService:
    user_repository: UserRepository
    user_cache_repository: UserCacheRepository

    async def get_all_users(self) -> list[User]:
        return await self.user_repository.get_all_users()

    async def get_user_by_id(self, user_id: int) -> UserDTO:

        if (user := await self.user_cache_repository.get_user_by_id(user_id=user_id)) is not None:
            return user

        user = await self.user_repository.get_user_by_id(user_id=user_id)

        await self.user_cache_repository.set_user_to_cache(
            data=UserDTO(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                is_active=user.is_active,
            )
        )
        return user

    async def update_user_info(self, user_data: UpdateUserRequestDTO, user_id: int) -> None:
        await self.user_repository.update_user_info(user_id=user_id, user_data=user_data)

    async def delete_user(self, user_id: int) -> None:
        await self.user_repository.delete_user_by_id(user_id=user_id)
