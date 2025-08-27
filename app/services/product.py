from typing import Annotated

from fastapi import Depends, Path, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.helpers.category import get_category_by_id
from app.helpers.product import (
    build_product_query_with_filters,
    get_product_by_id,
)
from app.helpers.validation import validate_non_empty_body
from app.models.product import Product
from app.schemas.product import PriceSort, ProductCreate, ProductUpdate


async def get_products_with_filters_service(
    session: AsyncSession = Depends(get_async_session),
    category_id: Annotated[int | None, Query(gt=0)] = None,
    title: Annotated[str | None, Query(min_length=3, max_length=100)] = None,
    sort_price: Annotated[
        PriceSort | None, Query(description="asc - по возрастанию, desc - по убыванию")
    ] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
):
    """Сервис для получения товаров с фильтрацией, сортировкой и пагинацией.

    Args:
        session: Асинхронная сессия БД
        category_id: ID категории для фильтрации
        title: Поиск по названию товара
        sort_price: Сортировка по цене (asc/desc)
        offset: Смещение для пагинации
        limit: Лимит для пагинации

    Returns:
        Список товаров с загруженными категориями
    """
    if category_id:
        # проверяем есть ли такая категория
        category = await get_category_by_id(
            category_id=category_id,
            session=session,
        )

    query = build_product_query_with_filters(
        category_id=category_id,
        title=title,
        sort_price=sort_price,
        offset=offset,
        limit=limit,
    )

    result = await session.execute(query)

    return result.scalars().all()


async def create_product_service(
    data: ProductCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Сервис для создания товаров

    Args:
        data (ProductCreate): Данные для создания товара
        session (AsyncSession, optional): Асинхронная сессия БД. Defaults to Depends(get_async_session).

    Returns:
        Созданный товар
    """
    try:
        # проверяем есть ли такая категория
        category = await get_category_by_id(
            category_id=data.category_id,
            session=session,
        )

        product = Product(**data.model_dump(exclude_unset=True))

        session.add(product)
        await session.commit()
        await session.refresh(product)

        product = await get_product_by_id(
            product_id=product.id,
            session=session,
        )

        return product

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла ошибка при создании товара",
        )


async def update_product_service(
    product_id: Annotated[int, Path(title="ID товара", ge=1)],
    data: ProductUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Сервис для обновление данных товара

    Args:
        data (ProductUpdate): Данные для обновления товара
        product_id (Annotated[int, Path, optional): ID товара. Defaults to "ID товара", ge=1)].
        session (AsyncSession, optional): Асинхронная сессия БД. Defaults to Depends(get_async_session).

    Returns:
        Обновленный товар
    """
    try:
        update_data = validate_non_empty_body(data)

        product = await get_product_by_id(
            product_id=product_id,
            session=session,
        )

        if "category_id" in update_data:
            category = await get_category_by_id(
                category_id=update_data["category_id"],
                session=session,
            )

        for key, value in update_data.items():
            setattr(product, key, value)

        await session.commit()
        await session.refresh(product)

        return product

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла внутренняя ошибка сервера",
        )


async def delete_product_service(
    product_id: Annotated[int, Path(ge=1)],
    session: AsyncSession = Depends(get_async_session),
):
    """Сервис для удаления товара

    Args:
        product_id (Annotated[int, Path, optional): ID товара. Defaults to 1)].
        session (AsyncSession, optional): Асинхронная сессия БД. Defaults to Depends(get_async_session).
    """
    try:
        product = await get_product_by_id(
            product_id=product_id,
            session=session,
        )

        await session.delete(product)
        await session.commit()

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла внутренняя ошибка сервера",
        )
