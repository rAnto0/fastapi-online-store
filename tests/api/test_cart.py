import pytest

from tests.helpers import assert_cart_item_in_db


@pytest.mark.asyncio
async def test_get_empty_cart(auth_client_non_admin):
    """Получение пустой корзины"""
    resp = await auth_client_non_admin.get("/cart/")
    assert resp.status_code == 200
    data = resp.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_cart_with_items(
    auth_client_non_admin, product_factory, cart_add_item_factory
):
    """Получение корзины с товарами"""
    product1 = await product_factory(title="Product 1", price=10.0, stock_quantity=10)
    product2 = await product_factory(title="Product 2", price=20.0, stock_quantity=5)

    item1_data = await cart_add_item_factory(product1.id, quantity=2)
    await auth_client_non_admin.post("/cart/add", json=item1_data)

    item2_data = await cart_add_item_factory(product2.id, quantity=1)
    await auth_client_non_admin.post("/cart/add", json=item2_data)

    resp = await auth_client_non_admin.get("/cart/")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) == 2
    for item in data:
        assert "id" in item
        assert "quantity" in item
        assert "product" in item
        assert "title" in item["product"]
        assert "price" in item["product"]


@pytest.mark.asyncio
async def test_add_product_to_cart_success(
    auth_client_non_admin, product_factory, cart_add_item_factory, db_session
):
    """Успешное добавление товара в корзину"""
    product = await product_factory(title="Test Product", price=15.0, stock_quantity=10)

    add_data = await cart_add_item_factory(product.id, quantity=3)

    resp = await auth_client_non_admin.post("/cart/add", json=add_data)
    assert resp.status_code == 201
    data = resp.json()

    assert data["quantity"] == 3
    assert data["product"]["id"] == product.id
    assert data["product"]["title"] == "Test Product"

    await assert_cart_item_in_db(
        db_session=db_session, product_id=product.id, expected_quantity=3
    )


@pytest.mark.asyncio
async def test_add_product_insufficient_stock(
    auth_client_non_admin, product_factory, cart_add_item_factory
):
    """Попытка добавить больше товара, чем есть в наличии"""
    product = await product_factory(
        title="Limited Product", price=15.0, stock_quantity=2
    )

    add_data = await cart_add_item_factory(product.id, quantity=5)

    resp = await auth_client_non_admin.post("/cart/add", json=add_data)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_add_product_twice_updates_quantity(
    auth_client_non_admin, product_factory, cart_add_item_factory, db_session
):
    """Повторное добавление того же товара увеличивает количество"""
    product = await product_factory(title="Test Product", stock_quantity=10)

    # Первое добавление
    add_data = await cart_add_item_factory(product.id, quantity=2)
    resp = await auth_client_non_admin.post("/cart/add", json=add_data)
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 2

    # Второе добавление того же товара
    add_data = await cart_add_item_factory(product.id, quantity=3)
    resp = await auth_client_non_admin.post("/cart/add", json=add_data)
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 5


@pytest.mark.asyncio
async def test_update_product_quantity_success(
    auth_client_non_admin,
    product_factory,
    cart_add_item_factory,
    cart_update_quantity_factory,
):
    """Успешное обновление количества товара"""
    product = await product_factory(title="Test Product", stock_quantity=10)

    add_data = await cart_add_item_factory(product.id, quantity=2)
    await auth_client_non_admin.post("/cart/add", json=add_data)

    update_data = cart_update_quantity_factory(quantity=5)
    resp = await auth_client_non_admin.patch(
        f"/cart/item/{product.id}", json=update_data
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity"] == 5


@pytest.mark.asyncio
async def test_update_product_quantity_to_zero_removes_item(
    auth_client_non_admin,
    product_factory,
    cart_add_item_factory,
    cart_update_quantity_factory,
):
    """Установка количества в 0 удаляет товар из корзины"""
    product = await product_factory(title="Test Product", stock_quantity=10)

    add_data = await cart_add_item_factory(product.id, quantity=2)
    await auth_client_non_admin.post("/cart/add", json=add_data)

    update_data = cart_update_quantity_factory(quantity=0)
    resp = await auth_client_non_admin.patch(
        f"/cart/item/{product.id}", json=update_data
    )
    assert resp.status_code == 204

    resp = await auth_client_non_admin.get("/cart/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_update_nonexistent_product(
    auth_client_non_admin, cart_update_quantity_factory
):
    """Попытка обновить несуществующий товар в корзине"""
    update_data = cart_update_quantity_factory(quantity=5)
    resp = await auth_client_non_admin.patch("/cart/item/999", json=update_data)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_from_cart(
    auth_client_non_admin, product_factory, cart_add_item_factory
):
    """Удаление конкретного товара из корзины"""
    product1 = await product_factory(title="Product 1", stock_quantity=10)
    product2 = await product_factory(title="Product 2", stock_quantity=5)

    await auth_client_non_admin.post(
        "/cart/add", json=await cart_add_item_factory(product1.id)
    )
    await auth_client_non_admin.post(
        "/cart/add", json=await cart_add_item_factory(product2.id)
    )

    resp = await auth_client_non_admin.get("/cart/")
    assert len(resp.json()) == 2

    resp = await auth_client_non_admin.delete(f"/cart/item/{product1.id}")
    assert resp.status_code == 204

    resp = await auth_client_non_admin.get("/cart/")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["product"]["id"] == product2.id


@pytest.mark.asyncio
async def test_delete_nonexistent_product_from_cart(auth_client_non_admin):
    """Попытка удалить несуществующий товар из корзины"""
    resp = await auth_client_non_admin.delete("/cart/item/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_clear_cart(
    auth_client_non_admin, product_factory, cart_add_item_factory
):
    """Полная очистка корзины"""
    product1 = await product_factory(title="Product 1", stock_quantity=10)
    product2 = await product_factory(title="Product 2", stock_quantity=5)

    await auth_client_non_admin.post(
        "/cart/add", json=await cart_add_item_factory(product1.id)
    )
    await auth_client_non_admin.post(
        "/cart/add", json=await cart_add_item_factory(product2.id)
    )

    resp = await auth_client_non_admin.get("/cart/")
    assert len(resp.json()) == 2

    resp = await auth_client_non_admin.delete("/cart/clear")
    assert resp.status_code == 204

    resp = await auth_client_non_admin.get("/cart/")
    assert resp.status_code == 200
    data = resp.json()
    assert data == []


@pytest.mark.asyncio
async def test_clear_empty_cart(auth_client_non_admin):
    """Очистка пустой корзины"""
    resp = await auth_client_non_admin.delete("/cart/clear")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_cart_unauthorized_access(async_client):
    """Попытка доступа к корзине без аутентификации"""
    endpoints = [
        ("GET", "/cart/"),
        ("POST", "/cart/add"),
        ("PATCH", "/cart/item/1"),
        ("DELETE", "/cart/item/1"),
        ("DELETE", "/cart/clear"),
    ]

    for method, endpoint in endpoints:
        if method == "GET":
            resp = await async_client.get(endpoint)
        elif method == "POST":
            resp = await async_client.post(
                endpoint, json={"product_id": 1, "quantity": 1}
            )
        elif method == "PATCH":
            resp = await async_client.patch(endpoint, json={"quantity": 1})
        else:
            resp = await async_client.delete(endpoint)

        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_cart_item_stock_validation(
    auth_client_non_admin,
    product_factory,
    cart_add_item_factory,
    cart_update_quantity_factory,
):
    """Проверка валидации количества товара при обновлении"""
    product = await product_factory(title="Limited Product", stock_quantity=3)

    # Добавляем максимальное количество
    add_data = await cart_add_item_factory(product.id, quantity=3)
    resp = await auth_client_non_admin.post("/cart/add", json=add_data)
    assert resp.status_code == 201

    # Пытаемся увеличить количество сверх доступного
    update_data = cart_update_quantity_factory(quantity=5)
    resp = await auth_client_non_admin.patch(
        f"/cart/item/{product.id}", json=update_data
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cart_persistence_across_requests(
    auth_client_non_admin, product_factory, cart_add_item_factory
):
    """Проверка сохранности корзины между запросами"""
    product = await product_factory(title="Test Product", stock_quantity=10)

    add_data = await cart_add_item_factory(product.id, quantity=2)
    resp = await auth_client_non_admin.post("/cart/add", json=add_data)
    assert resp.status_code == 201

    for _ in range(3):
        resp = await auth_client_non_admin.get("/cart/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["quantity"] == 2
        assert data[0]["product"]["id"] == product.id
