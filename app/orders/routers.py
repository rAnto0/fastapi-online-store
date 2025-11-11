from typing import Annotated
from fastapi import APIRouter, Depends, Path, status

from app.auth.services import validate_user_admin_service
from .schemas import OrderCreate, OrderRead, OrderStatus
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
    return await order_service.get_orders_by_status(
        order_status=OrderStatus.PENDING, offset=offset, limit=limit
    )


@router.get(
    "/confirmed/",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderRead],
    dependencies=admin_deps,
    summary="Получить подтвержденные заказы (только для админов)",
)
async def get_orders_confirmed(
    offset: int = 0,
    limit: int = 100,
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_orders_by_status(
        order_status=OrderStatus.CONFIRMED, offset=offset, limit=limit
    )


@router.get(
    "/processing/",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderRead],
    dependencies=admin_deps,
    summary="Получить заказы в обработке (только для админов)",
)
async def get_orders_processing(
    offset: int = 0,
    limit: int = 100,
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_orders_by_status(
        order_status=OrderStatus.PROCESSING, offset=offset, limit=limit
    )


@router.get(
    "/shipped/",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderRead],
    dependencies=admin_deps,
    summary="Получить заказы в доставке (только для админов)",
)
async def get_orders_shipped(
    offset: int = 0,
    limit: int = 100,
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_orders_by_status(
        order_status=OrderStatus.SHIPPED, offset=offset, limit=limit
    )


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
    return await order_service.update_order_status(
        order_id=order_id,
        new_status=OrderStatus.CONFIRMED,
        expected_current_status=OrderStatus.PENDING,
    )


@router.patch(
    "/{order_id}/processing/",
    response_model=OrderRead,
    dependencies=admin_deps,
    summary="Начать сборку товара (только для админов)",
)
async def start_processing_order(
    order_id: Annotated[int, Path(ge=1)],
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.update_order_status(
        order_id=order_id,
        new_status=OrderStatus.PROCESSING,
        expected_current_status=OrderStatus.CONFIRMED,
    )


@router.patch(
    "/{order_id}/shipped/",
    response_model=OrderRead,
    dependencies=admin_deps,
    summary="Начать доставку товара (только для админов)",
)
async def start_shipped_order(
    order_id: Annotated[int, Path(ge=1)],
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.update_order_status(
        order_id=order_id,
        new_status=OrderStatus.SHIPPED,
        expected_current_status=OrderStatus.PROCESSING,
    )


@router.patch(
    "/{order_id}/delivered/",
    response_model=OrderRead,
    dependencies=admin_deps,
    summary="Заказ доставлен (только для админов)",
)
async def delivered_order(
    order_id: Annotated[int, Path(ge=1)],
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.delivered_order(order_id=order_id)


@router.patch(
    "/{order_id}/cancel/",
    response_model=OrderRead,
    summary="Отменить заказ",
)
async def cancel_order(
    order_id: Annotated[int, Path(ge=1)],
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.cancel_order(order_id=order_id)
