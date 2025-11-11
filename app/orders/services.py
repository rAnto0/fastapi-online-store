from typing import Sequence

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.cart.models import CartItem
from app.cart.validations import validate_non_empty_cart
from app.cart.services import delete_cart_service
from app.products.models import Product
from app.users.schemas import UserRead
from app.auth.services import get_current_auth_user
from .schemas import (
    DeliveryAddressAdd,
    OrderCreate,
    OrderItemCreate,
    OrderStatus,
    PaymentMethods,
    PaymentStatus,
)
from .models import DeliveryAddress, Order, OrderItem


class OrderService:
    """Сервис для работы с заказами пользователя

    Предоставляет методы для создания, получения и управления заказами пользователей.
    Занимается проверкой заказов, обработкой платежей и управлением запасами.

    Attributes:
        user (UserRead): Авторизованный пользователь
        session (AsyncSession): Асинхронная сессия БД
    """

    def __init__(self, user: UserRead, session: AsyncSession):
        self.user = user
        self.session = session

    async def create_order(self, data: OrderCreate):
        """Сервис - создать заказ

        Args:
            data (OrderCreate): Данные для создания заказа

        Raises:
            HTTPException: 404 - Если корзина не найдена
            HTTPException: 400 - Если товара нет в наличии
            HTTPException: 500 - При внутренних ошибках сервера

        Returns:
            Order: Заказ
        """
        try:
            outer = self.session.in_transaction()
            tx_ctx = self.session.begin_nested() if outer else self.session.begin()

            async with tx_ctx:
                # проверяем что корзина не пустая
                cart_item = await validate_non_empty_cart(
                    user_id=self.user.id, session=self.session
                )
                # создаем заказ, без товаров и общей цены
                order = await self._create_order(data)
                # рассчитываем общую цену и записываем в заказ(так же проверяем каждый товар на наличие и создаем snapshot товара)
                await self._create_order_item_from_cart(
                    order=order, cart_item=cart_item
                )
                # создаем адресс доставки
                await self._create_delivery_address(
                    order_id=order.id, data=data.delivery_address
                )
                # очищаем корзину(без коммита)
                await delete_cart_service(
                    user=self.user,
                    session=self.session,
                    commit=False,
                    flush=True,
                    rollback=False,
                )

                if data.payment_method == PaymentMethods.CASH:
                    pass

                elif data.payment_method == PaymentMethods.CARD:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Оплата картой пока невозможна",
                    )
                    # Инициируем процесс оплаты через платежный шлюз
                    # payment_url = await self._initiate_payment(order)

                    # Возвращаем URL для перенаправления на страницу оплаты
                    # return {"order_id": order.id, "payment_url": payment_url}

            # коммит внешней транзакции
            if outer:
                await self.session.commit()

            return await self.get_order_auth_user_by_id(
                order_id=order.id,
                error_detail="Заказ не найден после создания",
            )

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Произошла непредвиденная ошибка при создании заказа: {e}",
            )

    async def get_orders_auth_user(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Order]:
        """Сервис - получить все заказы пользователя

        Args:
            offset (int, optional): Количество пропускаемых записей. Defaults to 0.
            limit (int, optional): Максимальное количество возвращаемых записей. Defaults to 100.

        Raises:
            HTTPException: 404 - У пользователя нет заказов

        Returns:
            Sequence[Order]: Список заказов
        """
        query = (
            select(Order)
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.product)
                .selectinload(Product.category),
                selectinload(Order.delivery_address),
            )
            .where(Order.user_id == self.user.id)
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        orders = result.scalars().all()

        if not orders:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказов нет",
            )

        return orders

    async def get_order_auth_user_by_id(
        self,
        order_id: int,
        error_detail: str = "Заказ не найден",
    ) -> Order:
        """Сервис - получить заказ по его ID(заказа)

        Args:
            order_id (int): ID заказа
            error_detail (str, optional): Описание ошибки. Defaults to "Заказ не найден".

        Raises:
            HTTPException: 404 заказ не найден

        Returns:
            Order: Заказ пользователя
        """
        query = (
            select(Order)
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.product)
                .selectinload(Product.category),
                selectinload(Order.delivery_address),
            )
            .where(Order.id == order_id, Order.user_id == self.user.id)
        )
        result = await self.session.execute(query)
        order = result.scalars().first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_detail,
            )

        return order

    async def get_orders_by_status(
        self,
        order_status: OrderStatus,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Order]:
        """Сервис - получить заказ по статусу (admin)

        Args:
            offset (int, optional): Количество пропускаемых записей. Defaults to 0.
            limit (int, optional): Максимальное количество возвращаемых записей. Defaults to 100.

        Raises:
            HTTPException: 404 - Нет заказов

        Returns:
            Sequence[Order]: Список заказов
        """
        query = (
            select(Order)
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.product)
                .selectinload(Product.category),
                selectinload(Order.delivery_address),
            )
            .where(Order.order_status == order_status)
            .order_by(Order.created_at.asc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        orders = result.scalars().all()

        if not orders:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказов нет",
            )

        return orders

    async def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        expected_current_status: OrderStatus,
        error_detail: str = "Заказ не найден",
    ) -> Order:
        """Сервис - обновить статус заказа с проверкой текущего статуса

        Args:
            order_id (int): ID заказа
            new_status (OrderStatus): Новый статус заказа
            expected_current_status (OrderStatus): Ожидаемый текущий статус для валидации
            error_detail (str, optional): Описание ошибки. Defaults to "Заказ не найден".

        Raises:
            HTTPException: 404 заказ не найден
            HTTPException: 400 неверный текущий статус

        Returns:
            Order: Обновленный заказ
        """
        order = await self._get_order_by_order_id(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_detail
            )

        if order.order_status != expected_current_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Невозможно изменить статус на {new_status}. "
                    f"Текущий статус {order.order_status}, ожидался {expected_current_status}"
                ),
            )

        order.order_status = new_status

        await self.session.commit()
        await self.session.refresh(order)

        return order

    async def delivered_order(
        self,
        order_id: int,
        error_detail: str = "Заказ не найден",
    ) -> Order:
        """Сервис - доставить заказ (courier)"""
        order = await self.update_order_status(
            order_id=order_id,
            new_status=OrderStatus.DELIVERED,
            expected_current_status=OrderStatus.SHIPPED,
            error_detail=error_detail,
        )

        # Обновляем статус оплаты если был pending (наличные)
        if order.payment_status == PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.COMPLETED

        await self.session.commit()
        await self.session.refresh(order)

        return order

    async def cancel_order(
        self,
        order_id: int,
        error_detail: str = "Заказ не найден",
    ) -> Order:
        """Сервис - отменить заказ"""
        order = await self._get_order_by_order_id(order_id)

        if not order:
            raise HTTPException(status_code=404, detail=error_detail)

        # Разлогика отмены в зависимости от статуса оплаты
        if order.payment_status == PaymentStatus.COMPLETED:
            order.payment_status = PaymentStatus.REFUNDED
        else:
            order.payment_status = PaymentStatus.FAILED

        order.order_status = OrderStatus.CANCELLED

        # TODO: Разрезервировать товары
        # await self._release_reserved_products(order)

        await self.session.commit()
        await self.session.refresh(order)

        return order

    async def _create_order(
        self,
        data: OrderCreate,
        shipping_price: int = 200,
    ) -> Order:
        """Вспомогательная функция - создать заказ

        Args:
            data (OrderCreate): Данные для создания заказа
            shipping_price (int, optional): Цена доставки. Defaults to 200.

        Returns:
            Order: Созданный заказ
        """
        order = Order(
            user_id=self.user.id,
            subtotal=0,
            shipping_price=shipping_price,
            total=shipping_price,
            payment_method=data.payment_method,
            notes=data.notes,
            order_status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
        )
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)

        return order

    async def _create_order_item_from_cart(
        self,
        order: Order,
        cart_item: Sequence[CartItem],
    ):
        """Вспомогательная функция - перенести товары из корзины в заказ

        Args:
            order (Order): Заказ куда перенести
            cart_item (Sequence[CartItem]): Товары из корзины
        """
        subtotal: float = 0  # сумма всех товаров
        for item in cart_item:
            # атомарно зарезервировать количество в БД
            stmt = (
                update(Product)
                .where(
                    Product.id == item.product_id,
                    (Product.stock_quantity - Product.reserved) >= item.quantity,
                )
                .values(reserved=Product.reserved + item.quantity)
                .returning(Product.id)
            )

            result = await self.session.execute(stmt)
            product_id = result.scalar_one_or_none()
            if product_id is None:
                # резерв не прошёл — недостаточно доступного количества
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Товар отсутствует на складе",
                        "product_id": item.product_id,
                    },
                )

            await self._create_order_item(
                OrderItemCreate(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_title=item.product.title,
                    product_price=item.product.price,
                    quantity=item.quantity,
                )
            )
            subtotal += item.quantity * item.product.price

        order.subtotal = subtotal
        order.total = float(order.total) + subtotal

        await self.session.flush()
        await self.session.refresh(order)

    async def _create_order_item(self, data: OrderItemCreate):
        """Вспомогательная функция - создать объект OrderItem на основе CartItem

        Args:
            data (OrderItemCreate): Данные для создания OrderItem
        """
        order_item = OrderItem(**data.model_dump())
        self.session.add(order_item)

        await self.session.flush()
        await self.session.refresh(order_item)

    async def _create_delivery_address(self, order_id: int, data: DeliveryAddressAdd):
        """Вспомогательная функция - создать объект адреса доставки определенного заказа

        Args:
            order_id (int): ID заказа
            data (DeliveryAddressAdd): Адресс доставки
        """
        delivery_address = DeliveryAddress(
            order_id=order_id, **data.model_dump(exclude_unset=True)
        )
        self.session.add(delivery_address)

        await self.session.flush()
        await self.session.refresh(delivery_address)

    async def _get_order_by_order_id(self, order_id: int) -> Order | None:
        """Вспомогательная функция для загрузки заказа со связями"""
        query = (
            select(Order)
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.product)
                .selectinload(Product.category),
                selectinload(Order.delivery_address),
            )
            .where(Order.id == order_id)
        )
        result = await self.session.execute(query)

        return result.scalars().first()


async def get_order_service(
    user: UserRead = Depends(get_current_auth_user),
    session: AsyncSession = Depends(get_async_session),
) -> OrderService:
    """Фабрика для создания экземпляра OrderService с внедренными зависимостями

    Args:
        user (UserRead): Аутентифицированный пользователь
        session (AsyncSession): Асинхронная сессия БД

    Returns:
        OrderService: Экземпляр сервиса заказов
    """
    return OrderService(user=user, session=session)
