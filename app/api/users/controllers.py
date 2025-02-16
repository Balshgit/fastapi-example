from dependency_injector.wiring import inject
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import NoResultFound
from starlette import status
from starlette.responses import JSONResponse, Response

from app.api.users.deps import request_verification
from app.api.users.serializers import DetailedUserSerializer, UpdateUserSerializer, UserSerializer
from app.core.users.dto import UpdateUserRequestDTO
from app.core.users.services import UserService
from app.di.app_dependency_injector import AsyncProvide, DIContainer

router = APIRouter()


@router.get(
    "/users",
    name="users:get_users",
    status_code=status.HTTP_200_OK,
    response_class=JSONResponse,
    response_model=list[UserSerializer],
    dependencies=[Depends(request_verification)],
    summary="Получение всех пользователей",
)
@inject
async def get_users(
    user_service: UserService = Depends(AsyncProvide[DIContainer.services.user_service]),
) -> JSONResponse:
    """Получить список всех пользователей"""
    users = await user_service.get_all_users()

    data = [UserSerializer.model_validate(user).model_dump() for user in users]

    return JSONResponse(status_code=status.HTTP_200_OK, content=data)


@router.get(
    "/users/{user_id}",
    name="users:get_users",
    status_code=status.HTTP_200_OK,
    response_class=JSONResponse,
    response_model=DetailedUserSerializer,
    dependencies=[Depends(request_verification)],
    summary="Получение всех пользователей",
)
@inject
async def get_all_users(
    user_id: int,
    user_service: UserService = Depends(AsyncProvide[DIContainer.services.user_service]),
) -> JSONResponse:
    """Получить список всех пользователей"""

    try:
        user = await user_service.get_user_by_id(user_id=user_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail=f"User with user_id {user_id} not found") from exc

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=DetailedUserSerializer.model_validate(user).model_dump(),
    )


@router.put(
    "/users/{user_id}",
    name="users:get_users",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(request_verification)],
    summary="Изменение данных пользователя",
)
@inject
async def update_user_info(
    user_id: int,
    user_data: UpdateUserSerializer = Body(...),
    user_service: UserService = Depends(AsyncProvide[DIContainer.services.user_service]),
) -> None:
    """Изменить данные пользователя"""

    data = UpdateUserRequestDTO(**user_data.model_dump())
    await user_service.update_user_info(user_data=data, user_id=user_id)


@router.delete(
    "/users/{user_id}",
    name="users:get_users",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(request_verification)],
    summary="Удаление пользователя",
)
@inject
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(AsyncProvide[DIContainer.services.user_service]),
) -> None:
    """Изменить данные пользователя"""

    await user_service.delete_user(user_id=user_id)
