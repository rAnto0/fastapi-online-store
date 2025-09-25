import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.categories.models import Category
from tests.helpers import assert_category_in_db


@pytest.mark.asyncio
async def test_get_categories(
    async_client: AsyncClient,
    category_factory,
):
    cat1 = await category_factory()
    cat2 = await category_factory()

    resp = await async_client.get("/category/")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) == 2

    assert data[0]["name"] == cat1.name
    assert data[1]["name"] == cat2.name


@pytest.mark.asyncio
async def test_get_categories_pagination(
    async_client: AsyncClient,
    category_factory,
):
    for i in range(15):
        await category_factory()

    resp = await async_client.get("/category/?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5


@pytest.mark.asyncio
async def test_get_category_by_id(
    async_client: AsyncClient,
    category_factory,
):
    cat1 = await category_factory()
    cat2 = await category_factory()

    resp = await async_client.get(f"/category/{cat2.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["description"] == cat2.description
    assert data["name"] == cat2.name


@pytest.mark.asyncio
async def test_get_category_by_invalid_id(
    async_client: AsyncClient,
):
    resp = await async_client.get("/category/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_category_admin(
    async_client: AsyncClient,
    db_session,
    override_admin_dependency,
    category_payload_factory,
):
    payload = category_payload_factory()

    resp = await async_client.post("/category/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == payload["description"]
    assert data["name"] == payload["name"]

    await assert_category_in_db(db_session, payload["name"], payload["description"])


@pytest.mark.asyncio
async def test_create_category_edge_cases(
    async_client: AsyncClient,
    override_admin_dependency,
    category_payload_factory,
):
    # Тест с очень длинным названием
    long_name = "A" * 100
    payload = category_payload_factory(name=long_name)
    resp = await async_client.post("/category/", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_category_non_auth(
    async_client: AsyncClient,
    category_payload_factory,
):
    payload = category_payload_factory()

    resp = await async_client.post("/category/", json=payload)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_category_non_admin(
    auth_client_non_admin,
    category_payload_factory,
):
    payload = category_payload_factory()

    resp = await auth_client_non_admin.post("/category/", json=payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_category_success(
    async_client: AsyncClient,
    category_factory,
    override_admin_dependency,
):
    """Успешное обновление категории администратором"""
    category = await category_factory(
        name="Original Name",
        description="Original Description",
    )

    update_data = {
        "name": "Updated Name",
        "description": "Updated Description",
    }

    resp = await async_client.patch(f"/category/{category.id}", json=update_data)
    assert resp.status_code == 200
    data = resp.json()

    # Проверяем обновленные данные в ответе
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated Description"
    assert data["id"] == category.id  # ID не должен меняться


@pytest.mark.asyncio
async def test_update_category_partial(
    async_client: AsyncClient,
    category_factory,
    override_admin_dependency,
    db_session,
):
    """Частичное обновление категории (только одно поле)"""
    category = await category_factory(
        name="Original Name", description="Original Description"
    )

    # Обновляем только цену
    update_data = {"description": "Updated Description"}

    resp = await async_client.patch(f"/category/{category.id}", json=update_data)
    assert resp.status_code == 200
    data = resp.json()

    # Проверяем, что обновилась только цена
    assert data["name"] == "Original Name"
    assert data["description"] == "Updated Description"


@pytest.mark.asyncio
async def test_update_category_not_found(
    async_client: AsyncClient,
    override_admin_dependency,
):
    """Обновление несуществующей категории"""
    update_data = {"name": "Updated Name"}

    resp = await async_client.patch("/category/99999", json=update_data)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_category_empty_body(
    async_client: AsyncClient,
    category_factory,
    override_admin_dependency,
):
    """Обновление с пустым телом запроса"""
    category = await category_factory()

    resp = await async_client.patch(f"/category/{category.id}", json={})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_category_non_auth(
    async_client: AsyncClient,
    category_factory,
):
    """Обновление категории неаутентифицированным пользователем"""
    category = await category_factory()

    update_data = {"name": "Updated Name"}
    resp = await async_client.patch(f"/category/{category.id}", json=update_data)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_category_non_admin(
    auth_client_non_admin,
    category_factory,
):
    """Обновление категории не-администратором"""
    category = await category_factory()

    update_data = {"name": "Updated Name"}
    resp = await auth_client_non_admin.patch(
        f"/category/{category.id}", json=update_data
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_category_database_consistency(
    async_client: AsyncClient,
    category_factory,
    override_admin_dependency,
    db_session,
):
    """Проверка согласованности данных в БД после обновления"""
    category = await category_factory(name="Original", description="Desc")

    update_data = {"name": "Updated in DB", "description": "Updated Desc"}

    resp = await async_client.patch(f"/category/{category.id}", json=update_data)
    assert resp.status_code == 200

    # Проверяем, что данные действительно сохранились в БД
    result = await db_session.execute(
        select(Category).where(Category.id == category.id)
    )
    updated_category = result.scalars().first()

    assert updated_category.name == "Updated in DB"
    assert updated_category.description == "Updated Desc"


@pytest.mark.asyncio
async def test_delete_category_admin(
    async_client: AsyncClient,
    category_factory,
    override_admin_dependency,
):
    """Удаление категории с правами админа"""
    category = await category_factory()

    resp = await async_client.delete(f"/category/{category.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_category_non_admin(
    category_factory,
    auth_client_non_admin,
):
    """Удаление категории с без прав админа"""
    category = await category_factory()

    resp = await auth_client_non_admin.delete(f"/category/{category.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_category_non_auth(
    async_client: AsyncClient,
    category_factory,
):
    """Удаление категории неавторизованным"""
    category = await category_factory()

    resp = await async_client.delete(f"/category/{category.id}")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_delete_category_invalid_id(
    async_client: AsyncClient,
    override_admin_dependency,
):
    """Удаление категории с правами админа - невалидный ID"""
    resp = await async_client.delete("/category/99999")
    assert resp.status_code == 404
