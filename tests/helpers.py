import pytest
from sqlalchemy import select

from app.categories.models import Category
from app.core.security import verify_password
from app.products.models import Product
from app.users.models import User


async def assert_product_in_db(db_session, title, expected_price):
    """Утверждение: продукт с title существует и цена совпадает."""
    q = select(Product).where(Product.title == title)
    r = await db_session.execute(q)
    prod = r.scalars().first()
    assert prod is not None
    assert prod.price == pytest.approx(expected_price)


async def assert_category_in_db(db_session, name, desc):
    """Утверждение: категория с name существует и описание совпадает."""
    q = select(Category).where(Category.name == name)
    r = await db_session.execute(q)
    prod = r.scalars().first()
    assert prod is not None
    assert prod.description == desc


async def assert_user_in_db(db_session, username, email, password):
    """Утверждение: пользователь с username существует и данные совпадают."""
    result = await db_session.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    assert user is not None
    assert user.email == email
    assert verify_password(password, user.hashed_password) is None
    assert user.is_admin is False


async def assert_cart_item_in_db(db_session, product_id, expected_quantity):
    """Проверка наличия элемента корзины в БД"""
    from app.cart.models import CartItem

    q = select(CartItem).where(CartItem.product_id == product_id)
    r = await db_session.execute(q)
    cart_item = r.scalars().first()
    assert cart_item is not None
    assert cart_item.quantity == expected_quantity


@pytest.fixture
async def category(category_factory):
    """Создаёт уникальную категорию в БД и возвращает её."""
    return await category_factory()
