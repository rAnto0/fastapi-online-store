from fastapi import APIRouter, Depends, status

from app.schemas.cart import CartItemRead
from app.services.cart import add_product_cart_service, get_cart_service


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
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CartItemRead,
    summary="Добавить товар в корзину",
)
async def add_product_cart(
    cart_product: CartItemRead = Depends(add_product_cart_service),
):
    return cart_product
