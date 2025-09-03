from fastapi import APIRouter, Depends, Response, status

from .schemas import CartItemRead
from .services import (
    add_product_cart_service,
    delete_cart_service,
    delete_product_from_cart_service,
    get_cart_service,
    update_product_quantity_from_cart_service,
)


router = APIRouter(prefix="/cart", tags=["Корзина"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[CartItemRead],
    summary="Получить корзину пользователя",
)
async def get_cart(
    cart_item: list[CartItemRead] = Depends(get_cart_service),
):
    return cart_item


@router.post(
    "/add",
    status_code=status.HTTP_201_CREATED,
    response_model=CartItemRead,
    summary="Добавить товар в корзину",
)
async def add_product_cart(
    cart_product: CartItemRead = Depends(add_product_cart_service),
):
    return cart_product


@router.patch(
    "/item/{product_id}",
    summary="Изменить количество товара",
    responses={
        200: {
            "description": "Количество товара успешно обновлено",
            "model": CartItemRead,
        },
        204: {"description": "Товар удален из корзины (количество установлено в 0)"},
    },
)
async def update_product_quantity_from_cart(
    cart_product: CartItemRead | None = Depends(
        update_product_quantity_from_cart_service
    ),
):
    if cart_product is None:
        # Товар был удален из корзины - возвращаем 204 No Content
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # Товар был обновлен - возвращаем 200 OK с данными
    return cart_product


@router.delete(
    "/item/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить товар по ID продукта из корзины",
)
async def delete_product_from_cart(
    _: None = Depends(delete_product_from_cart_service),
):
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/clear",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Очистить корзину пользователя",
)
async def delete_cart(
    _: None = Depends(delete_cart_service),
):
    return Response(status_code=status.HTTP_204_NO_CONTENT)
