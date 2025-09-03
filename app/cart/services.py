from typing import Annotated

from fastapi import Body, Depends, HTTPException, Path, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.users import schemas as userSchemas
from app.products import (
    helpers as productHelper,
    validations as productValidation,
)
from app.auth.services import get_current_auth_user
from .schemas import CartAddProduct, CartItemQuantityUpdate
from .models import CartItem, Cart
from .helpers import (
    get_cart_by_user_id,
    get_or_create_cart_by_user_id,
    get_cart_id_by_user_id_or_error_404,
    get_cart_item_by_cart_id,
    get_cart_item_by_cart_id_and_product_id,
    get_cart_item_by_cart_id_and_product_id_or_error_404,
)


async def get_cart_service(
    user: userSchemas.UserRead = Depends(get_current_auth_user),
    session: AsyncSession = Depends(get_async_session),
):
    # получаем корзину по ID пользователя
    cart: Cart | None = await get_cart_by_user_id(
        user_id=user.id,
        session=session,
    )

    # Если корзины нет - возвращаем пустой список
    if cart is None:
        return []

    # получаем товары с корзины
    cart_item = await get_cart_item_by_cart_id(
        cart_id=cart.id,
        session=session,
    )

    return cart_item


async def add_product_cart_service(
    data: CartAddProduct,
    user: userSchemas.UserRead = Depends(get_current_auth_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        # получаем товар по ID товара
        product = await productHelper.get_product_by_id(
            product_id=data.product_id,
            session=session,
        )

        # получаем корзину по ID пользователя
        cart = await get_or_create_cart_by_user_id(
            user_id=user.id,
            session=session,
        )
        # Проверяем, есть ли товар уже в корзине
        cart_item = await get_cart_item_by_cart_id_and_product_id(
            cart_id=cart.id,
            product_id=product.id,
            session=session,
        )

        # Определяем общее количество
        total_quantity = data.quantity
        if cart_item:
            total_quantity += cart_item.quantity

        # Проверяем доступность товара
        productValidation.validate_product_in_stock(
            product=product, quantity=total_quantity
        )

        # Обновляем или добавляем товар в корзину
        if cart_item:
            cart_item.quantity = total_quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=data.product_id,
                quantity=data.quantity,
            )
            session.add(cart_item)

        await session.commit()
        await session.refresh(cart_item)

        cart_item = await get_cart_item_by_cart_id_and_product_id(
            cart_id=cart.id,
            product_id=product.id,
            session=session,
        )

        return cart_item

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла ошибка при добавлении товара в корзину",
        )


async def update_product_quantity_from_cart_service(
    product_id: Annotated[int, Path(ge=1)],
    data: Annotated[CartItemQuantityUpdate, Body()],
    user: userSchemas.UserRead = Depends(get_current_auth_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        cart_id = await get_cart_id_by_user_id_or_error_404(
            user_id=user.id,
            session=session,
        )

        cart_item = await get_cart_item_by_cart_id_and_product_id_or_error_404(
            cart_id=cart_id,
            product_id=product_id,
            session=session,
        )

        # Если quantity = 0, удаляем товар из корзины
        if data.quantity == 0:
            await session.delete(cart_item)
            await session.commit()

            return None

        # Обновляем количество
        productValidation.validate_product_in_stock(
            product=cart_item.product,
            quantity=data.quantity,
        )
        cart_item.quantity = data.quantity

        await session.commit()
        await session.refresh(cart_item)

        # Загружаем обновленные данные с связями
        updated_item = await get_cart_item_by_cart_id_and_product_id(
            cart_id=cart_id,
            product_id=product_id,
            session=session,
        )
        return updated_item

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла ошибка при добавлении товара в корзину",
        )


async def delete_product_from_cart_service(
    product_id: Annotated[int, Path(ge=1)],
    user: userSchemas.UserRead = Depends(get_current_auth_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        cart_id = await get_cart_id_by_user_id_or_error_404(
            user_id=user.id,
            session=session,
        )

        cart_item = await get_cart_item_by_cart_id_and_product_id_or_error_404(
            cart_id=cart_id,
            product_id=product_id,
            session=session,
        )

        await session.delete(cart_item)
        await session.commit()

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла внутренняя ошибка сервера",
        )


async def delete_cart_service(
    user: userSchemas.UserRead = Depends(get_current_auth_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        cart = await get_cart_by_user_id(
            user_id=user.id,
            session=session,
        )
        if cart is None:
            # Если корзины нет, она уже "пустая"
            return

        # Удаляем все элементы корзины, корзину оставляем
        await session.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        await session.commit()

    except Exception as e:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла внутренняя ошибка сервера",
        )
