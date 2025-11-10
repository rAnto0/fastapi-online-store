from typing import Annotated
from fastapi import APIRouter, Depends, Path, status

from app.auth.services import validate_user_admin_service
from .schemas import OrderCreate, OrderRead
from .services import OrderService, get_order_service


router = APIRouter(prefix="/orders", tags=["Заказ"])

admin_deps = [Depends(validate_user_admin_service)]


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


@router.get(
    "/pending/",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderRead],
    dependencies=admin_deps,
    summary="Получить заказы ожидающие подтверждения (только для админов)",
)
async def get_orders_pending(
    offset: int = 0,
    limit: int = 100,
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_orders_pending(offset=offset, limit=limit)


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


@router.patch(
    "/{order_id}/confirm/",
    response_model=OrderRead,
    dependencies=admin_deps,
    summary="Подтвердить заказ (только для админов)",
)
async def confirm_order(
    order_id: Annotated[int, Path(ge=1)],
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.confirm_order(order_id=order_id)
