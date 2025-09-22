import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import insert, select

from app.categories.models import Category
from app.products.models import Product


@pytest.fixture
def product_payload_factory():
    """Возвращает фабрику payload'ов — можно задавать title/price/stock через аргументы."""

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
async def category(db_session):
    """Создаёт уникальную категорию в БД и возвращает её."""
    name = f"Test Cat {uuid.uuid4().hex[:6]}"
    await db_session.execute(
        insert(Category).values(name=name, description="Test Description Cat")
    )
    await db_session.commit()

    result = await db_session.execute(select(Category).where(Category.name == name))
    cat = result.scalars().first()
    return cat


async def assert_product_in_db(db_session, title, expected_price):
    """Утверждение: продукт с title существует и цена совпадает."""
    q = select(Product).where(Product.title == title)
    r = await db_session.execute(q)
    prod = r.scalars().first()
    assert prod is not None
    assert prod.price == pytest.approx(expected_price)


@pytest.mark.asyncio
async def test_admin_create_product(
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
async def test_non_auth_create_product(
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
async def test_non_admin_create_product(
    db_session, auth_client_non_admin, category, product_payload_factory
):
    payload = product_payload_factory(category.id)

    resp = await auth_client_non_admin.post("/products/", json=payload)
    assert resp.status_code == 403, resp.text
    data = resp.json()
    assert data["detail"] == "Недостаточно прав для выполнения операции"
