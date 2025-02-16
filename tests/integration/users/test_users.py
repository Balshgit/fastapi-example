import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.users.models import User
from app.core.users.repositories import UserRepository
from tests.integration.factories.users import UserFactory
from tests.utils import RaiseError

pytestmark = [
    pytest.mark.asyncio,
]


async def test_get_users_for_not_authorized_user(
    rest_client: AsyncClient,
) -> None:
    response = await rest_client.get("/api/users")
    assert response.status_code == 403


async def test_get_users_empty_list(
    sync_db: Session,
    user_client: AsyncClient,
) -> None:
    response = await user_client.get("/api/users")
    assert response.status_code == 200
    data = response.json()

    assert data == []


async def test_get_users(
    sync_db: Session,
    user_client: AsyncClient,
) -> None:
    users = UserFactory.create_batch(size=3)
    user_1, user_2, user_3 = sorted(users, key=lambda u: u.id)

    response = await user_client.get("/api/users")
    assert response.status_code == 200

    data = response.json()

    assert data == [
        {
            "id": user_1.id,
            "username": user_1.username,
            "first_name": user_1.first_name,
            "last_name": user_1.last_name,
        },
        {
            "id": user_2.id,
            "username": user_2.username,
            "first_name": user_2.first_name,
            "last_name": user_2.last_name,
        },
        {
            "id": user_3.id,
            "username": user_3.username,
            "first_name": user_3.first_name,
            "last_name": user_3.last_name,
        },
    ]


async def test_get_users_by_id_not_found(
    sync_db: Session,
    user_client: AsyncClient,
) -> None:
    user = UserFactory()
    not_existing_user_id = user.id + 9999

    response = await user_client.get(f"/api/users/{not_existing_user_id}")
    assert response.status_code == 404


async def test_get_users_by_id(
    sync_db: Session,
    user_client: AsyncClient,
) -> None:
    user = UserFactory()

    response = await user_client.get(f"/api/users/{user.id}")
    assert response.status_code == 200

    data = response.json()

    assert data == {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": user.is_active,
    }


async def test_update_users_by_id_for_anonym(
    sync_db: Session,
    rest_client: AsyncClient,
) -> None:
    user = UserFactory()
    response = await rest_client.put(f"/api/users/{user.id}", json={"username": "Вася"})
    assert response.status_code == 403


async def test_update_users_by_id(
    sync_db: Session,
    user_client: AsyncClient,
) -> None:
    user = UserFactory()

    response = await user_client.put(f"/api/users/{user.id}", json={"username": "Вася"})
    assert response.status_code == 204

    sync_db.refresh(user)
    updated_user = sync_db.execute(select(User).where(User.id == user.id)).scalar()

    assert updated_user.username == "Вася"


async def test_update_users_by_id_with_incorrect_email(
    sync_db: Session,
    user_client: AsyncClient,
) -> None:
    user = UserFactory()
    username = user.username

    response = await user_client.put(f"/api/users/{user.id}", json={"username": "Вася", "email": "not_valid_email@."})
    assert response.status_code == 422

    sync_db.refresh(user)
    updated_user = sync_db.execute(select(User).where(User.id == user.id)).scalar()

    assert updated_user.username == username
    assert updated_user.username != "Вася"


async def test_get_user_from_cache(
    sync_db: Session,
    user_client: AsyncClient,
    mocker: MockFixture,
) -> None:
    user = UserFactory()

    response = await user_client.get(f"/api/users/{user.id}")
    assert response.status_code == 200

    mocker.patch.object(UserRepository, UserRepository.get_user_by_id.__name__, side_effect=RaiseError())

    response = await user_client.get(f"/api/users/{user.id}")
    assert response.status_code == 200

    data = response.json()

    assert data == {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": user.is_active,
    }


async def test_delete_user_for_anonym(
    sync_db: Session,
    rest_client: AsyncClient,
) -> None:
    users = UserFactory.create_batch(size=3)

    response = await rest_client.delete(f"/api/users/{users[0]}")
    assert response.status_code == 403

    users = sync_db.execute(select(User)).all()
    assert len(users) == 3


async def test_delete_not_existing_user(
    sync_db: Session,
    user_client: AsyncClient,
) -> None:
    UserFactory.create_batch(size=3)

    response = await user_client.delete("/api/users/9999")
    assert response.status_code == 204

    users = sync_db.execute(select(User)).all()

    assert len(users) == 3


async def test_delete_user(
    sync_db: Session,
    user_client: AsyncClient,
) -> None:
    user = UserFactory()
    UserFactory.create_batch(size=2)

    response = await user_client.delete(f"/api/users/{user.id}")
    assert response.status_code == 204

    deleted_user = sync_db.execute(select(User).where(User.id == user.id)).scalar()
    assert deleted_user is None

    users = sync_db.execute(select(User)).all()

    assert len(users) == 2
    assert user not in users
