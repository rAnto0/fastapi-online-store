from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductRead, ProductCreate, ProductUpdate


router = APIRouter(prefix="/products", tags=["Товары"])


@router.get(
    "/", response_model=list[ProductRead], summary="Получить список всех товаров"
)
async def get_products(
    session: AsyncSession = Depends(get_async_session),
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
):
    query = (
        select(Product)
        .options(selectinload(Product.category))
        .order_by(Product.id)
        .offset(offset)
        .limit(limit)
    )
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
    summary="Создать товар",
)
async def create_product(
    data: ProductCreate, session: AsyncSession = Depends(get_async_session)
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
