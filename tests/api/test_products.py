import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.helpers import assert_product_in_db
from app.products.models import Product


@pytest.mark.asyncio
async def test_get_product(
    async_client: AsyncClient,
    product_factory,
):
    product1 = await product_factory(price=10.0)
    product2 = await product_factory(price=20.0)

    resp = await async_client.get("/products/")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) == 2

    assert data[0]["price"] == 10.0
    assert data[1]["price"] == 20.0


@pytest.mark.asyncio
async def test_get_products_sorted(
    async_client: AsyncClient,
    product_factory,
):
    product2 = await product_factory(price=20.0)
    product1 = await product_factory(price=10.0)

    resp = await async_client.get("/products/")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) == 2

    prices = {item["price"] for item in data}
    assert prices == {10.0, 20.0}

    resp = await async_client.get("/products/?sort_price=desc")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) == 2

    prices = {item["price"] for item in data}
    assert prices == {20.0, 10.0}


@pytest.mark.asyncio
async def test_get_products_pagination(
    async_client: AsyncClient,
    product_factory,
):
    for i in range(15):
        await product_factory(price=float(i + 1))

    resp = await async_client.get("/products/?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5


@pytest.mark.asyncio
async def test_get_product_by_id(
    async_client: AsyncClient,
    product_factory,
):
    product1 = await product_factory(price=10.0)
    product2 = await product_factory(price=20.0)

    resp = await async_client.get(f"/products/{product2.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["price"] == 20.0
    assert data["title"] == product2.title


@pytest.mark.asyncio
async def test_get_product_by_invalid_id(
    async_client: AsyncClient,
):
    resp = await async_client.get("/products/99999")
    assert resp.status_code == 404
    data = resp.json()

    assert data["detail"] == "Товар не найден"


@pytest.mark.asyncio
async def test_create_product_admin(
    async_client: AsyncClient,
    db_session,
    override_admin_dependency,
    category,
    product_payload_factory,
):
    payload = product_payload_factory(category.id)

    resp = await async_client.post("/products/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == payload["title"]
    assert data["price"] == payload["price"]
    assert data["category"]["id"] == category.id

    await assert_product_in_db(db_session, payload["title"], payload["price"])


@pytest.mark.asyncio
async def test_create_product_edge_cases(
    async_client: AsyncClient,
    override_admin_dependency,
    category,
    product_payload_factory,
):
    # Тест с минимальной ценой
    payload = product_payload_factory(category.id, price=0.01)
    resp = await async_client.post("/products/", json=payload)
    assert resp.status_code == 201

    # Тест с большим количеством
    payload = product_payload_factory(category.id, stock_quantity=999)
    resp = await async_client.post("/products/", json=payload)
    assert resp.status_code == 201

    # Тест с очень длинным названием
    long_title = "A" * 100
    payload = product_payload_factory(category.id, title=long_title)
    resp = await async_client.post("/products/", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_product_validation_errors(
    async_client: AsyncClient,
    override_admin_dependency,
    category,
):
    # Отрицательная цена
    payload = {
        "title": "Test",
        "description": "desc",
        "price": -10.0,  # Невалидно
        "category_id": category.id,
        "stock_quantity": 10,
    }
    resp = await async_client.post("/products/", json=payload)
    assert resp.status_code == 422

    # Отсутствует обязательное поле
    payload = {
        "description": "desc",
        "price": 10.0,
        "category_id": category.id,
        "stock_quantity": 10,
    }
    resp = await async_client.post("/products/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_product_non_auth(
    async_client: AsyncClient,
    category,
    product_payload_factory,
):
    payload = product_payload_factory(category.id)

    resp = await async_client.post("/products/", json=payload)
    assert resp.status_code == 401, resp.text
    data = resp.json()
    assert data["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_product_non_admin(
    auth_client_non_admin,
    category,
    product_payload_factory,
):
    payload = product_payload_factory(category.id)

    resp = await auth_client_non_admin.post("/products/", json=payload)
    assert resp.status_code == 403, resp.text
    data = resp.json()
    assert data["detail"] == "Недостаточно прав для выполнения операции"


@pytest.mark.asyncio
async def test_update_product_success(
    async_client: AsyncClient,
    product_factory,
    override_admin_dependency,
):
    """Успешное обновление товара администратором"""
    product = await product_factory(
        title="Original Title",
        price=10.0,
        description="Original Description",
        stock_quantity=5,
    )

    update_data = {
        "title": "Updated Title",
        "price": 15.0,
        "description": "Updated Description",
        "stock_quantity": 20,
    }

    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 200
    data = resp.json()

    # Проверяем обновленные данные в ответе
    assert data["title"] == "Updated Title"
    assert data["price"] == 15.0
    assert data["description"] == "Updated Description"
    assert data["stock_quantity"] == 20
    assert data["id"] == product.id  # ID не должен меняться


@pytest.mark.asyncio
async def test_update_product_partial(
    async_client: AsyncClient,
    product_factory,
    override_admin_dependency,
    db_session,
):
    """Частичное обновление товара (только одно поле)"""
    product = await product_factory(
        title="Original Title", price=10.0, description="Original Description"
    )

    # Обновляем только цену
    update_data = {"price": 25.0}

    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 200
    data = resp.json()

    # Проверяем, что обновилась только цена
    assert data["price"] == 25.0
    assert data["title"] == "Original Title"
    assert data["description"] == "Original Description"


@pytest.mark.asyncio
async def test_update_product_change_category(
    async_client: AsyncClient,
    product_factory,
    category,
    override_admin_dependency,
    db_session,
):
    """Обновление категории товара"""
    product = await product_factory()

    update_data = {"category_id": category.id}

    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 200
    data = resp.json()

    # Проверяем, что категория обновилась
    assert data["category"]["id"] == category.id
    assert data["category"]["name"] == category.name


@pytest.mark.asyncio
async def test_update_product_not_found(
    async_client: AsyncClient,
    override_admin_dependency,
):
    """Обновление несуществующего товара"""
    update_data = {"title": "Updated Title"}

    resp = await async_client.patch("/products/99999", json=update_data)
    assert resp.status_code == 404
    data = resp.json()
    assert data["detail"] == "Товар не найден"


@pytest.mark.asyncio
async def test_update_product_invalid_category(
    async_client: AsyncClient,
    product_factory,
    override_admin_dependency,
):
    """Обновление с несуществующей категорией"""
    product = await product_factory()

    update_data = {"category_id": 99999}

    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 404
    data = resp.json()
    assert data["detail"] == "Категория не найдена"


@pytest.mark.asyncio
async def test_update_product_validation_errors(
    async_client: AsyncClient,
    product_factory,
    override_admin_dependency,
):
    """Обновление с невалидными данными"""
    product = await product_factory()

    # Отрицательная цена
    update_data = {"price": -10.0}
    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 422

    # Отрицательное количество
    update_data = {"stock_quantity": -5}
    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 422

    # Пустой title
    update_data = {"title": ""}
    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_product_empty_body(
    async_client: AsyncClient,
    product_factory,
    override_admin_dependency,
):
    """Обновление с пустым телом запроса"""
    product = await product_factory()

    resp = await async_client.patch(f"/products/{product.id}", json={})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_product_non_auth(
    async_client: AsyncClient,
    product_factory,
):
    """Обновление товара неаутентифицированным пользователем"""
    product = await product_factory()

    update_data = {"title": "Updated Title"}
    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 401
    data = resp.json()
    assert data["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_product_non_admin(
    auth_client_non_admin,
    product_factory,
):
    """Обновление товара не-администратором"""
    product = await product_factory()

    update_data = {"title": "Updated Title"}
    resp = await auth_client_non_admin.patch(
        f"/products/{product.id}", json=update_data
    )
    assert resp.status_code == 403
    data = resp.json()
    assert data["detail"] == "Недостаточно прав для выполнения операции"


@pytest.mark.asyncio
async def test_update_product_database_consistency(
    async_client: AsyncClient,
    product_factory,
    override_admin_dependency,
    db_session,
):
    """Проверка согласованности данных в БД после обновления"""
    product = await product_factory(title="Original", price=10.0)

    update_data = {"title": "Updated in DB", "price": 99.99, "stock_quantity": 50}

    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 200

    # Проверяем, что данные действительно сохранились в БД
    result = await db_session.execute(select(Product).where(Product.id == product.id))
    updated_product = result.scalars().first()

    assert updated_product.title == "Updated in DB"
    assert updated_product.price == 99.99
    assert updated_product.stock_quantity == 50


@pytest.mark.asyncio
async def test_update_product_edge_cases(
    async_client: AsyncClient,
    product_factory,
    override_admin_dependency,
):
    """Граничные случаи обновления"""
    product = await product_factory()

    # Максимально длинное название
    long_title = "A" * 100
    update_data = {"title": long_title}
    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 200

    # Минимальная цена
    update_data = {"price": 0.1}
    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 200

    # Максимальное количество
    update_data = {"stock_quantity": 999}
    resp = await async_client.patch(f"/products/{product.id}", json=update_data)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_product_admin(
    async_client: AsyncClient,
    product_factory,
    override_admin_dependency,
):
    """Удаление продукта с правами админа"""
    product = await product_factory()

    resp = await async_client.delete(f"/products/{product.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_product_non_admin(
    product_factory,
    auth_client_non_admin,
):
    """Удаление продукта с правами админа"""
    product = await product_factory()

    resp = await auth_client_non_admin.delete(f"/products/{product.id}")
    assert resp.status_code == 403

    data = resp.json()
    assert data["detail"] == "Недостаточно прав для выполнения операции"


@pytest.mark.asyncio
async def test_delete_product_non_auth(
    async_client: AsyncClient,
    product_factory,
):
    """Удаление продукта с правами админа"""
    product = await product_factory()

    resp = await async_client.delete(f"/products/{product.id}")
    assert resp.status_code == 401

    data = resp.json()
    assert data["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_product_invalid_id(
    async_client: AsyncClient,
    override_admin_dependency,
):
    """Удаление продукта с правами админа"""
    resp = await async_client.delete("/products/99999")
    assert resp.status_code == 404

    data = resp.json()
    assert data["detail"] == "Товар не найден"
