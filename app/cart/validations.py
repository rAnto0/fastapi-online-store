from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CartItem
from .helpers import (
    get_cart_id_by_user_id_or_error_404,
    get_cart_item_by_cart_id_or_error_404,
)


async def validate_non_empty_cart(
    user_id: int,
    session: AsyncSession,
) -> Sequence[CartItem]:
    """Проверка что корзина не пустая

    Args:
        user_id (int): ID пользователя
        session (AsyncSession): Асинхронная сессия БД

    Raises:
        HTTPException: 404 - Если корзины нет или пустая

    Returns:
        Sequence[CartItem]: Список товаров из корзины
    """
    cart_id = await get_cart_id_by_user_id_or_error_404(
        user_id=user_id,
        session=session,
    )
    cart_item = await get_cart_item_by_cart_id_or_error_404(
        cart_id=cart_id,
        session=session,
    )

    return cart_item
