import uuid

import pytest

from app.categories.models import Category
from app.products.models import Product


@pytest.fixture
async def category_factory(db_session):
    """Возвращает фабрику категорий"""

    async def _factory(**kwargs):
        name = kwargs.get("name") or f"Test Cat {uuid.uuid4().hex[:6]}"
        description = kwargs.get("description") or "Test Description Cat"

        category = Category(name=name, description=description)
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
