import pytest
from sqlalchemy import select

from app.categories.models import Category
from app.products.models import Product


async def assert_product_in_db(db_session, title, expected_price):
    """Утверждение: продукт с title существует и цена совпадает."""
    q = select(Product).where(Product.title == title)
    r = await db_session.execute(q)
    prod = r.scalars().first()
    assert prod is not None
    assert prod.price == pytest.approx(expected_price)


async def assert_category_in_db(db_session, name, desc):
    """Утверждение: продукт с title существует и цена совпадает."""
    q = select(Category).where(Category.name == name)
    r = await db_session.execute(q)
    prod = r.scalars().first()
    assert prod is not None
    assert prod.description == desc


@pytest.fixture
async def category(category_factory):
    """Создаёт уникальную категорию в БД и возвращает её."""
    return await category_factory()
