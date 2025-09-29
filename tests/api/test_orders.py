import pytest
from sqlalchemy import select

from app.cart.models import Cart, CartItem
from app.orders.models import Order
from app.orders.schemas import OrderStatus, PaymentStatus
from app.products.models import Product


@pytest.mark.asyncio
async def test_get_orders_list_success(
    auth_client_non_admin,
    non_admin_user,
    product_factory,
    cart_item_factory,
    order_create_data_factory,
):
    """Получение списка заказов пользователя"""
    # Создаем заказ
    product = await product_factory(title="Test Product")
    await cart_item_factory(user=non_admin_user, product=product)
    order_create_data = order_create_data_factory()
    await auth_client_non_admin.post("/orders/create", json=order_create_data)

    # Получаем список заказов
    resp = await auth_client_non_admin.get("/orders/")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data) >= 1
    assert data[0]["payment_method"] == "cash"
    assert data[0]["order_status"] == OrderStatus.PENDING.value
    assert data[0]["payment_status"] == PaymentStatus.PENDING.value


@pytest.mark.asyncio
async def test_get_orders_list_empty(
    auth_client_non_admin,
):
    """Получение пустого списка заказов"""
    resp = await auth_client_non_admin.get("/orders/")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_order_by_id_success(
    auth_client_non_admin,
    non_admin_user,
    product_factory,
    cart_item_factory,
    order_create_data_factory,
):
    """Получение конкретного заказа по ID"""
    # Создаем заказ
    product = await product_factory(title="Test Product")
    await cart_item_factory(user=non_admin_user, product=product)
    order_create_data = order_create_data_factory()
    create_resp = await auth_client_non_admin.post(
        "/orders/create", json=order_create_data
    )
    order_id = create_resp.json()["id"]

    # Получаем заказ по ID
    resp = await auth_client_non_admin.get(f"/orders/{order_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == order_id
    assert data["payment_method"] == "cash"
    assert len(data["order_items"]) == 1
    assert data["order_items"][0]["product_title"] == "Test Product"


@pytest.mark.asyncio
async def test_get_order_by_id_not_found(
    auth_client_non_admin,
):
    """Получение несуществующего заказа"""
    resp = await auth_client_non_admin.get("/orders/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_order_by_id_unauthorized_user(
    auth_client_non_admin,
    admin_user,
    product_factory,
    cart_factory,
    db_session,
):
    """Попытка получить заказ другого пользователя"""
    # Создаем заказ от имени admin_user
    product = await product_factory()
    cart = await cart_factory(user=admin_user)
    cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
    db_session.add(cart_item)
    await db_session.flush()

    order = Order(
        user_id=admin_user.id,
        subtotal=10.0,
        shipping_price=200,
        total=210.0,
        payment_method="cash",
    )
    db_session.add(order)
    await db_session.flush()

    # Пытаемся получить заказ от имени non_admin_user
    resp = await auth_client_non_admin.get(f"/orders/{order.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_order_success(
    auth_client_non_admin,
    non_admin_user,
    product_factory,
    cart_item_factory,
    order_create_data_factory,
):
    """Успешное создание заказа"""
    product = await product_factory(title="Test Product")
    await cart_item_factory(user=non_admin_user, product=product)

    order_create_data = order_create_data_factory()
    resp = await auth_client_non_admin.post("/orders/create", json=order_create_data)
    assert resp.status_code == 201

    data = resp.json()
    assert data["payment_method"] == "cash"
    assert data["order_items"][0]["product_title"] == "Test Product"


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(
    auth_client_non_admin,
    non_admin_user,
    product_factory,
    cart_factory,
    order_create_data_factory,
    db_session,
):
    """Создание заказа при превышающем количество товара в корзине"""
    product = await product_factory(stock_quantity=1)
    cart = await cart_factory(user=non_admin_user)
    # вручную добавим cart_item с quantity=2
    cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=2)
    db_session.add(cart_item)
    await db_session.flush()
    await db_session.refresh(cart_item)

    order_create_data = order_create_data_factory()
    resp = await auth_client_non_admin.post("/orders/create", json=order_create_data)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_order_empty_cart(
    auth_client_non_admin,
    order_create_data_factory,
):
    """Создание заказа с пустой корзиной"""
    order_create_data = order_create_data_factory()
    resp = await auth_client_non_admin.post("/orders/create", json=order_create_data)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_order_calculates_totals_correctly(
    auth_client_non_admin,
    non_admin_user,
    product_factory,
    cart_factory,
    cart_item_factory,
    order_create_data_factory,
    db_session,
):
    """Проверка корректного расчета сумм в заказе"""
    # Создаем два товара с разными ценами
    product1 = await product_factory(price=10.0)
    product2 = await product_factory(price=20.0)

    # Добавляем в корзину разные количества
    cart = await cart_factory(user=non_admin_user)
    await cart_item_factory(
        cart=cart, user=non_admin_user, product=product1, quantity=4
    )
    await cart_item_factory(
        cart=cart, user=non_admin_user, product=product2, quantity=2
    )

    order_create_data = order_create_data_factory()
    resp = await auth_client_non_admin.post("/orders/create", json=order_create_data)
    assert resp.status_code == 201

    data = resp.json()
    # Проверяем расчеты
    assert data["subtotal"] == 80.0
    assert data["shipping_price"] == 200
    assert data["total"] == 280.0


@pytest.mark.asyncio
async def test_create_order_reserves_products(
    auth_client_non_admin,
    non_admin_user,
    product_factory,
    cart_item_factory,
    order_create_data_factory,
    db_session,
):
    """Проверка резервирования товаров при создании заказа"""
    product = await product_factory()

    await cart_item_factory(user=non_admin_user, product=product, quantity=3)
    order_create_data = order_create_data_factory()

    resp = await auth_client_non_admin.post("/orders/create", json=order_create_data)
    assert resp.status_code == 201

    # Проверяем, что товар зарезервирован
    result = await db_session.execute(select(Product).where(Product.id == product.id))
    updated_product = result.scalars().first()
    assert updated_product.reserved == 3
    assert updated_product.stock_quantity == 10


@pytest.mark.asyncio
async def test_create_order_clears_cart(
    auth_client_non_admin,
    non_admin_user,
    product_factory,
    cart_item_factory,
    order_create_data_factory,
    db_session,
):
    """Проверка очистки корзины после создания заказа"""
    product = await product_factory()
    await cart_item_factory(user=non_admin_user, product=product, quantity=2)

    # Проверяем, что корзина не пуста
    cart_result = await db_session.execute(
        select(CartItem).join(Cart).where(Cart.user_id == non_admin_user.id)
    )
    cart_items_before = cart_result.scalars().all()
    assert len(cart_items_before) == 1

    order_create_data = order_create_data_factory()
    resp = await auth_client_non_admin.post("/orders/create", json=order_create_data)
    assert resp.status_code == 201

    # Проверяем, что корзина очищена
    cart_result = await db_session.execute(
        select(CartItem).join(Cart).where(Cart.user_id == non_admin_user.id)
    )
    cart_items_after = cart_result.scalars().all()
    assert len(cart_items_after) == 0


@pytest.mark.asyncio
async def test_create_order_multiple_products(
    auth_client_non_admin,
    non_admin_user,
    product_factory,
    cart_factory,
    cart_item_factory,
    order_create_data_factory,
):
    """Создание заказа с несколькими товарами"""
    # Создаем несколько товаров
    products = [
        await product_factory(title=f"Product {i}", price=i * 10.0) for i in range(1, 4)
    ]

    # Добавляем все в корзину
    cart = await cart_factory(user=non_admin_user)
    for product in products:
        await cart_item_factory(cart=cart, user=non_admin_user, product=product)

    order_create_data = order_create_data_factory()
    resp = await auth_client_non_admin.post("/orders/create", json=order_create_data)
    assert resp.status_code == 201

    data = resp.json()
    assert len(data["order_items"]) == 3

    # Проверяем, что все товары присутствуют в заказе
    product_titles = {item["product_title"] for item in data["order_items"]}
    expected_titles = {"Product 1", "Product 2", "Product 3"}
    assert product_titles == expected_titles


@pytest.mark.asyncio
async def test_create_order_unauthorized(
    async_client,
    order_create_data_factory,
):
    """Попытка создать заказ без аутентификации"""
    order_create_data = order_create_data_factory()
    resp = await async_client.post("/orders/create", json=order_create_data)
    assert resp.status_code == 401
