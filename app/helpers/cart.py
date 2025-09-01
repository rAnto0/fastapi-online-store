from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartItem
from app.models.product import Product


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
