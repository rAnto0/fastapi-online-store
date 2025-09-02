from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import PriceSort


def build_product_base_query(with_category: bool = True, product_id: int | None = None):
    """
    Строит базовый SQL-запрос для получения товара.
    """
    query = select(Product)
    if with_category:
        query = query.options(selectinload(Product.category))
    if product_id:
        query = query.where(Product.id == product_id)

    return query


def build_product_query_with_filters(
    category_id: int | None = None,
    title: str | None = None,
    sort_price: PriceSort | None = None,
    offset: int = 0,
    limit: int = 100,
):
    """
    Строит SQL-запрос для получения товаров с учетом фильтров, сортировки и пагинации.
    """
    # формируем основной запрос
    query = build_product_base_query(with_category=True)

    # добавляем к запросу сортировку по цене, если клиент запросил. Иначе сортировка по id
    if sort_price == PriceSort.asc:
        query = query.order_by(Product.price.asc())
    elif sort_price == PriceSort.desc:
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.id)

    # добавляем к запросу фильтрацию по категории, если клиент передал id категории
    if category_id:
        query = query.where(Product.category_id == category_id)

    # добавляем к запросу поиск по названию товара
    if title:
        query = query.filter(Product.title.ilike(f"%{title}%"))

    # добавляем к запросу пагинацию
    query = query.offset(offset).limit(limit)

    return query


async def get_product_by_id(
    product_id: int,
    session: AsyncSession,
) -> Product:
    """
    Фукнция для получения товара по ID.
    """
    query = build_product_base_query(product_id=product_id)
    result = await session.execute(query)

    product = result.scalars().first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар не найден",
        )

    return product
