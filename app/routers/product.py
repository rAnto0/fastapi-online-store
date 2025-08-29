from typing import Annotated

from fastapi import APIRouter, Depends, Response, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.helpers.product import get_product_by_id
from app.schemas.product import ProductRead
from app.services.auth import validate_user_admin_service
from app.services.product import (
    create_product_service,
    delete_product_service,
    get_products_with_filters_service,
    update_product_service,
)


router = APIRouter(prefix="/products", tags=["Товары"])


admin_deps = [Depends(validate_user_admin_service)]


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[ProductRead],
    summary="Получить список всех товаров",
)
async def get_products(
    products: list[ProductRead] = Depends(get_products_with_filters_service),
):
    """
    Получить список товаров с возможностью фильтрации, сортировки и пагинации.
    """
    return products


@router.get(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProductRead,
    summary="Получить товар по ID",
)
async def get_product(
    product_id: Annotated[int, Path(title="ID товара", ge=1)],
    session: AsyncSession = Depends(get_async_session),
):
    product = await get_product_by_id(
        product_id=product_id,
        session=session,
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
    product: ProductRead = Depends(create_product_service),
):
    return product


@router.patch(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProductRead,
    dependencies=admin_deps,
    summary="Обновить товар по ID",
)
async def update_product(product: ProductRead = Depends(update_product_service)):
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=admin_deps,
    summary="Удалить товар по ID",
)
async def delete_product(_: None = Depends(delete_product_service)):
    return Response(status_code=status.HTTP_204_NO_CONTENT)
