from typing import Annotated
from fastapi import APIRouter, Depends, Path, status

from .schemas import OrderCreate, OrderRead
from .services import OrderService, get_order_service


router = APIRouter(prefix="/orders", tags=["Заказ"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderRead],
    summary="Получить все заказы пользователя",
)
async def get_orders(
    offset: int = 0,
    limit: int = 100,
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_orders_auth_user(offset=offset, limit=limit)


@router.get(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=OrderRead,
    summary="Получить заказ по его ID",
)
async def get_order(
    order_id: Annotated[int, Path(ge=1)],
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_order_auth_user_by_id(order_id=order_id)


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderRead,
    summary="Создать заказ",
)
async def create_order(
    data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.create_order(data)
