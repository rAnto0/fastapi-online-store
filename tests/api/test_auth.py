import pytest
from httpx import AsyncClient

from app.core.security import get_password_hash
from tests.helpers import assert_user_in_db


@pytest.mark.asyncio
async def test_register_user_success(
    async_client: AsyncClient,
    user_registration_data_factory,
    db_session,
):
    """Успешная регистрация пользователя"""
    registration_data = user_registration_data_factory()

    resp = await async_client.post("/auth/register", json=registration_data)
    assert resp.status_code == 201
    data = resp.json()

    assert data["username"] == registration_data["username"]
    assert data["email"] == registration_data["email"]
    assert "id" in data
    assert "hashed_password" not in data

    await assert_user_in_db(
        db_session=db_session,
        username=registration_data["username"],
        email=registration_data["email"],
        password=registration_data["password"],
    )


@pytest.mark.asyncio
async def test_register_user_duplicate_username(
    async_client: AsyncClient,
    user_factory,
    user_registration_data_factory,
):
    """Регистрация с существующим username"""
    existing_user = await user_factory(username="existing_user")

    registration_data = user_registration_data_factory(username="existing_user")

    resp = await async_client.post("/auth/register", json=registration_data)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_user_duplicate_email(
    async_client: AsyncClient,
    user_factory,
    user_registration_data_factory,
):
    """Регистрация с существующим email"""
    existing_user = await user_factory(email="existing@example.com")

    registration_data = user_registration_data_factory(email="existing@example.com")

    resp = await async_client.post("/auth/register", json=registration_data)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_user_validation_errors(
    async_client: AsyncClient,
    user_registration_data_factory,
):
    """Ошибки валидации при регистрации"""
    # Слишком короткий username
    data = user_registration_data_factory(username="ab")
    resp = await async_client.post("/auth/register", json=data)
    assert resp.status_code == 422

    # Неверный email
    data = user_registration_data_factory(email="invalid-email")
    resp = await async_client.post("/auth/register", json=data)
    assert resp.status_code == 422

    # Слишком короткий пароль
    data = user_registration_data_factory(password="12")
    resp = await async_client.post("/auth/register", json=data)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_user_success(
    async_client: AsyncClient,
    user_factory,
    user_login_data_factory,
):
    """Успешный вход пользователя"""
    password = "SecurePass123!"
    user = await user_factory(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash(password),
    )

    login_data = user_login_data_factory(username="testuser", password=password)

    resp = await async_client.post("/auth/login", data=login_data)
    assert resp.status_code == 200
    data = resp.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_login_user_wrong_password(
    async_client: AsyncClient,
    user_factory,
    user_login_data_factory,
):
    """Вход с неверным паролем"""
    user = await user_factory(username="testuser")

    login_data = user_login_data_factory(
        username="testuser", password="WrongPassword123!"
    )

    resp = await async_client.post("/auth/login", data=login_data)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_user_not_found(
    async_client: AsyncClient,
    user_login_data_factory,
):
    """Вход несуществующего пользователя"""
    login_data = user_login_data_factory(
        username="nonexistent", password="SomePass123!"
    )

    resp = await async_client.post("/auth/login", data=login_data)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_success(
    auth_client_non_admin,
    non_admin_user,
):
    """Успешное получение текущего пользователя"""
    resp = await auth_client_non_admin.get("/me")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == non_admin_user.id
    assert data["username"] == non_admin_user.username
    assert data["email"] == non_admin_user.email
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(
    async_client: AsyncClient,
):
    """Получение текущего пользователя без аутентификации"""
    resp = await async_client.get("/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(
    async_client: AsyncClient,
    user_factory,
    user_login_data_factory,
):
    """Успешное обновление токена"""
    password = "SecurePass123!"
    user = await user_factory(
        username="testuser", hashed_password=get_password_hash(password)
    )

    login_data = user_login_data_factory(username="testuser", password=password)
    login_resp = await async_client.post("/auth/login", data=login_data)
    refresh_token = (
        f"{login_resp.json()['token_type']} {login_resp.json()['refresh_token']}"
    )
    print(refresh_token)

    resp = await async_client.post(
        "/auth/refresh", headers={"Authorization": refresh_token}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(
    async_client: AsyncClient,
):
    """Обновление токена с невалидным refresh token"""
    resp = await async_client.post(
        "/auth/refresh", headers={"Authorization": "Bearer invalid_token"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoint_access(
    async_client: AsyncClient,
    admin_user,
    user_login_data_factory,
):
    """Проверка доступа к админским эндпоинтам"""
    password = "AdminPass123!"
    admin_user.hashed_password = get_password_hash(password)

    login_data = user_login_data_factory(
        username=admin_user.username, password=password
    )
    login_resp = await async_client.post("/auth/login", data=login_data)
    tokens = login_resp.json()

    headers = {"Authorization": f"{tokens['token_type']} {tokens['access_token']}"}
    data = {"name": "Admin Cat", "description": "Admin Desc"}
    # админский эндпоинт
    resp = await async_client.post(
        "/category/",
        headers=headers,
        json=data,
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_admin_endpoint_denied(
    auth_client_non_admin,
):
    """Проверка отказа в доступе к админским эндпоинтам для обычного пользователя"""
    data = {"name": "Admin Cat", "description": "Admin Desc"}
    # админский эндпоинт
    resp = await auth_client_non_admin.post(
        "/category/",
        json=data,
    )
    assert resp.status_code == 403
