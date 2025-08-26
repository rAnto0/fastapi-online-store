from typing import Annotated
from enum import Enum

from fastapi import APIRouter, Depends, Query, status, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductRead, ProductCreate, ProductUpdate
from app.services.auth import get_current_admin_user


router = APIRouter(prefix="/products", tags=["Товары"])


admin_deps = [Depends(get_current_admin_user)]


class PriceSort(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get(
    "/", response_model=list[ProductRead], summary="Получить список всех товаров"
)
async def get_products(
    session: AsyncSession = Depends(get_async_session),
    category_id: Annotated[int | None, Query(gt=0)] = None,
    title: Annotated[str | None, Query(min_length=3, max_length=100)] = None,
    sort_price: Annotated[
        PriceSort | None, Query(description="asc - по возрастанию, desc - по убыванию")
    ] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
):
    # формируем основной запрос
    query = select(Product).options(selectinload(Product.category))

    # добавляем к запросу сортировку по цене, если клиент запросил. Иначе сортировка по id
    if sort_price == PriceSort.asc:
        query = query.order_by(Product.price.asc())
    elif sort_price == PriceSort.desc:
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.id)

    # добавляем к запросу фильтрацию по категории, если клиент передал id категории
    if category_id:
        category = await session.get(Category, category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
            )
        query = query.where(Product.category_id == category_id)

    # добавляем к запросу поиск по названию товара
    if title:
        query = query.filter(Product.title.ilike(f"%{title}%"))

    # добавляем к запросу пагинацию
    query = query.offset(offset).limit(limit)

    result = await session.execute(query)

    return result.scalars().all()


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Получить товар по ID",
    responses={
        404: {"description": "Товар не найден"},
    },
)
async def get_product(
    product_id: Annotated[int, Path(title="ID товара", ge=1)],
    session: AsyncSession = Depends(get_async_session),
):
    query = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id)
    )
    result = await session.execute(query)
    product = result.scalars().first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Товар не найден"
        )

    return product


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ProductRead,
    dependencies=admin_deps,
    summary="Создать товар",
)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        category = await session.get(Category, data.category_id)
        if category is None:
            raise HTTPException(status_code=400, detail="Категория не найдена")

        product = Product(**data.model_dump(exclude_unset=True))

        session.add(product)
        await session.commit()
        await session.refresh(product)

        query = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product.id)
        )
        product = await session.execute(query)

        return product.scalars().first()

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла ошибка при создании товара",
        )


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=admin_deps,
    summary="Обновить товар по ID",
    responses={
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def update_product(
    product_id: Annotated[int, Path(title="ID товара", ge=1)],
    data: ProductUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пустое тело запроса",
            )
        query = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        result = await session.execute(query)
        product = result.scalars().first()
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден"
            )

        if "category_id" in update_data:
            category = await session.get(Category, update_data["category_id"])
            if not category:
                raise HTTPException(status_code=400, detail="Категория не найдена")

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


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=admin_deps,
    summary="Удалить товар по ID",
)
async def delete_product(
    product_id: Annotated[int, Path(ge=1)],
    session: AsyncSession = Depends(get_async_session),
):
    try:
        product = await session.get(Product, product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден"
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
