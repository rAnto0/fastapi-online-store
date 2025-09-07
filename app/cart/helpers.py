from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.products.models import Product
from .models import Cart, CartItem


async def get_cart_by_user_id(
    user_id: int,
    session: AsyncSession,
) -> Cart | None:
    """Получить корзину по ID пользователя

    Args:
        user_id (int): ID пользователя
        session (AsyncSession): Асинхронная сессия БД

    Returns:
        Cart | None: Корзина пользователя или None, если корзины нет
    """
    query = select(Cart).where(Cart.user_id == user_id)
    result = await session.execute(query)

    return result.scalars().first()


async def get_cart_id_by_user_id_or_error_404(
    user_id: int,
    session: AsyncSession,
    error_detail: str = "Корзина не найдена",
) -> int:
    """Получить ID корзины по ID пользователя

    Args:
        user_id (int): ID пользователя
        session (AsyncSession): Асинхронная сессия БД
        error_detail (str): Описание ошибки. Defaults to "Корзина не найдена"

    Raises:
        HTTPException: 404 - Если корзины нет

    Returns:
        int: ID корзины
    """
    cart = await get_cart_by_user_id(
        user_id=user_id,
        session=session,
    )
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail,
        )

    return cart.id


async def get_or_create_cart_by_user_id(
    user_id: int,
    session: AsyncSession,
) -> Cart:
    """Получить или создать корзину по ID пользователя

    Args:
        user_id (int): ID пользователя
        session (AsyncSession): Асинхронная сессия БД

    Returns:
        Cart: Корзина пользователя
    """
    query = select(Cart).where(Cart.user_id == user_id)
    result = await session.execute(query)

    cart = result.scalars().first()
    if cart is None:
        cart = Cart(user_id=user_id)

        session.add(cart)
        await session.commit()
        await session.refresh(cart)

    return cart


async def get_cart_item_by_cart_id(
    cart_id: int,
    session: AsyncSession,
):
    """Получить товары с корзины по ID корзины

    Args:
        cart_id (int): ID корзины
        session (AsyncSession): Асинхронная сессия БД

    Returns:
        list[CartItem]: Товары с корзины
    """
    query = (
        select(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.category))
        .where(CartItem.cart_id == cart_id)
    )
    result = await session.execute(query)

    return result.scalars().all()


async def get_cart_item_by_cart_id_or_error_404(
    cart_id: int,
    session: AsyncSession,
) -> Sequence[CartItem]:
    """Получить товары с корзины по ID корзины или ошибка 404

    Args:
        cart_id (int): ID корзины
        session (AsyncSession): Асинхронная сессия БД

    Raises:
        HTTPException: 404 - Если корзина пустая

    Returns:
        Sequence[CartItem]: Товары с корзины
    """
    query = (
        select(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.category))
        .where(CartItem.cart_id == cart_id)
    )
    result = await session.execute(query)
    cart_item = result.scalars().all()
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Корзина пустая",
        )

    return cart_item


async def get_cart_item_by_cart_id_and_product_id(
    cart_id: int,
    product_id: int,
    session: AsyncSession,
) -> CartItem | None:
    """Получить товар с корзины по ID корзины и ID товара

    Args:
        cart_id (int): ID корзины
        product_id (int): ID товара
        session (AsyncSession): Асинхронная сессия БД

    Returns:
        CartItem: Товар из корзины пользователя или None если товара нет
    """
    query = (
        select(CartItem)
        .options(joinedload(CartItem.product).joinedload(Product.category))
        .where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
    )
    result = await session.execute(query)

    cart_item: CartItem | None = result.scalars().first()

    return cart_item


async def get_cart_item_by_cart_id_and_product_id_or_error_404(
    cart_id: int,
    product_id: int,
    session: AsyncSession,
    error_detail: str = "Такого товара в корзине нет",
) -> CartItem:
    """Получить товар с корзины по ID корзины и ID товара или ошибка 404

    Args:
        cart_id (int): ID корзины
        product_id (int): ID товара
        session (AsyncSession): Асинхронная сессия БД
        error_detail (str, optional): Описание ошибки. Defaults to "Такого товара в корзине нет".

    Raises:
        HTTPException: 404 - Если товара нет в корзине

    Returns:
        CartItem: Товар с корзины
    """
    cart_item = await get_cart_item_by_cart_id_and_product_id(
        cart_id=cart_id,
        product_id=product_id,
        session=session,
    )
    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail,
        )

    return cart_item
