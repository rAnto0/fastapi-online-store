import uuid

import pytest

from app.cart.models import Cart, CartItem
from app.categories.models import Category
from app.core.security import get_password_hash
from app.products.models import Product
from app.users.models import User


@pytest.fixture
async def category_payload_factory():
    """Возвращает фабрику payload'ов для категорий"""

    def _factory(name=None, description="Test Description Cat"):
        name = name or f"Test Cat {uuid.uuid4().hex[:6]}"
        return {
            "name": name,
            "description": description,
        }

    return _factory


@pytest.fixture
async def category_factory(
    db_session,
    category_payload_factory,
):
    """Возвращает фабрику категорий"""

    async def _factory(**kwargs):
        payload = category_payload_factory(**kwargs)

        category = Category(**payload)
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        return category

    return _factory


@pytest.fixture
def product_payload_factory():
    """Возвращает фабрику payload'ов для товаров — можно задавать title/price/stock через аргументы."""

    def _factory(
        category_id, title=None, price=12.5, stock_quantity=10, description="desc"
    ):
        title = title or f"My product {uuid.uuid4().hex[:6]}"
        return {
            "title": title,
            "description": description,
            "price": price,
            "category_id": category_id,
            "stock_quantity": stock_quantity,
        }

    return _factory


@pytest.fixture
async def product_factory(
    db_session,
    category,
    product_payload_factory,
):
    """Возвращает фабрику продуктов"""

    async def _factory(**kwargs):
        payload = product_payload_factory(category_id=category.id, **kwargs)

        product = Product(**payload)
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        return product

    return _factory


@pytest.fixture
async def user_factory(db_session, faker):
    """Фабрика для создания тестовых пользователей"""

    async def _factory(**kwargs):
        defaults = {
            "username": f"testuser_{faker.user_name()}",
            "email": f"test_{faker.word()}@example.com",
            "hashed_password": get_password_hash("TestPass123!"),
            "is_admin": False,
        }
        user_data = {**defaults, **kwargs}

        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _factory


@pytest.fixture
async def admin_user_factory(db_session, faker):
    """Фабрика для создания тестовых администраторов"""

    async def _factory(**kwargs):
        defaults = {
            "username": f"admin_{faker.user_name()}",
            "email": f"admin_{faker.word()}@example.com",
            "hashed_password": get_password_hash("AdminPass123!"),
            "is_admin": True,
        }
        user_data = {**defaults, **kwargs}

        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _factory


@pytest.fixture
def user_registration_data_factory(faker):
    """Фабрика данных для регистрации пользователя"""

    def _factory(**kwargs):
        base_data = {
            "username": f"testuser_{faker.user_name()}",
            "email": f"test_{faker.word()}@example.com",
            "password": "SecurePass123!",
        }
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
def user_login_data_factory():
    """Фабрика данных для входа пользователя"""

    def _factory(**kwargs):
        base_data = {"username": "testuser", "password": "SecurePass123!"}
        return {**base_data, **kwargs}

    return _factory


@pytest.fixture
async def cart_factory(db_session, user_factory):
    """Фабрика для создания корзины"""

    async def _factory(**kwargs):
        user = kwargs.pop("user", None)
        if user is None:
            user = await user_factory()

        cart = Cart(user_id=user.id, **kwargs)
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)
        return cart

    return _factory


@pytest.fixture
async def cart_item_factory(db_session, cart_factory, product_factory):
    """Фабрика для создания элемента корзины"""

    async def _factory(**kwargs):
        cart = kwargs.pop("cart", None)
        product = kwargs.pop("product", None)

        if cart is None:
            cart = await cart_factory()
        if product is None:
            product = await product_factory()

        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=kwargs.pop("quantity", 1),
            **kwargs,
        )
        db_session.add(cart_item)
        await db_session.commit()
        await db_session.refresh(cart_item)
        return cart_item

    return _factory


@pytest.fixture
def cart_add_item_factory(product_factory):
    """Фабрика данных для добавления товара в корзину"""

    async def _factory(product_id, quantity=1):
        return {"product_id": product_id, "quantity": quantity}

    return _factory


@pytest.fixture
def cart_update_quantity_factory():
    """Фабрика данных для обновления количества товара"""

    def _factory(quantity=1):
        return {"quantity": quantity}

    return _factory
