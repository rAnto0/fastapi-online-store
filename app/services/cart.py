from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.helpers import cart as cartHelper, product as productHelper
from app.models.cart import CartItem, Cart
from app.schemas import cart as cartSchemas, user as userSchemas
from app.validation import product as productValidation
from app.services.auth import get_current_auth_user


async def get_cart_service(
    user: userSchemas.UserRead = Depends(get_current_auth_user),
    session: AsyncSession = Depends(get_async_session),
):
    # получаем корзину по ID пользователя
    cart: Cart | None = await cartHelper.get_cart_by_user_id(
        user_id=user.id,
        session=session,
    )

    # Если корзины нет - возвращаем пустой список
    if cart is None:
        return []

    # получаем товары с корзины
    cart_item = await cartHelper.get_cart_item_by_cart_id(
        cart_id=cart.id,
        session=session,
    )

    return cart_item


async def add_product_cart_service(
    data: cartSchemas.CartAddProduct,
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
        cart = await cartHelper.get_or_create_cart_by_user_id(
            user_id=user.id,
            session=session,
        )
        # Проверяем, есть ли товар уже в корзине
        cart_item = await cartHelper.get_cart_item_by_cart_id_and_product_id(
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

        cart_item = await cartHelper.get_cart_item_by_cart_id_and_product_id(
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
