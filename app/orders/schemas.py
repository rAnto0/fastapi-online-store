from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from app.products.schemas import ProductRead


class OrderStatus(str, Enum):
    PENDING = "pending"  # Ожидает подтверждения
    CONFIRMED = "confirmed"  # Подтвержден
    PROCESSING = "processing"  # В обработке/сборке
    SHIPPED = "shipped"  # Отправлен
    DELIVERED = "delivered"  # Доставлен
    CANCELLED = "cancelled"  # Отменен
    REFUNDED = "refunded"  # Возвращен


class PaymentStatus(str, Enum):
    PENDING = "pending"  # Ожидает оплаты
    PROCESSING = "processing"  # Платеж в обработке
    COMPLETED = "completed"  # Оплата завершена успешно
    FAILED = "failed"  # Ошибка оплаты
    REFUNDED = "refunded"  # Средства возвращены
    PARTIALLY_REFUNDED = "partially_refunded"  # Частичный возврат


class PaymentMethods(str, Enum):
    CARD = "card"  # оплата картой
    CASH = "cash"  # оплата наличными


class OrderBase(BaseModel):
    payment_method: PaymentMethods
    notes: Annotated[
        str | None, Field(min_length=4, max_length=50, description="Заметка к заказу")
    ] = None


class OrderItemBase(BaseModel):
    order_id: Annotated[int, Field(..., ge=1, description="ID заказа")]
    product_id: Annotated[int, Field(..., ge=1, description="ID товара")]
    product_title: Annotated[
        str,
        Field(
            ..., min_length=3, max_length=100, description="Название товара в момент"
        ),
    ]
    product_price: Annotated[
        float, Field(..., gt=0, description="Цена товара в момент заказа")
    ]
    quantity: Annotated[int, Field(..., ge=1, le=999, description="Количество товара")]


class OrderItemRead(OrderItemBase):
    id: int
    product: ProductRead

    @computed_field
    def total_price(self) -> float:
        """Общая стоимость позиции (quantity * product.price)"""
        return round(self.quantity * self.product.price, 2)

    model_config = {"from_attributes": True}


class OrderItemCreate(OrderItemBase):
    pass


# АДРЕС
class DeliveryAddressBase(BaseModel):
    city: Annotated[str, Field(..., min_length=4, max_length=50, description="Город")]
    postcode: Annotated[int | None, Field(ge=1000, le=4000, description="Почта")] = None
    region: Annotated[
        str | None, Field(min_length=4, max_length=50, description="Регион")
    ] = None
    country: Annotated[
        str, Field(..., min_length=4, max_length=50, description="Страна")
    ]
    phone: Annotated[
        str | None, Field(min_length=11, max_length=12, description="Регион")
    ] = None


class DeliveryAddressRead(DeliveryAddressBase):
    id: int
    order_id: int

    model_config = {"from_attributes": True}


class DeliveryAddressAdd(DeliveryAddressBase):
    pass


# ЗАКАЗ
class OrderRead(OrderBase):
    id: int
    order_status: OrderStatus
    payment_status: PaymentStatus

    subtotal: float
    shipping_price: float
    discount: float | None = None
    total: float
    payment_id: str | None = None

    created_at: datetime
    updated_at: datetime
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None

    delivery_address: DeliveryAddressRead
    order_items: list[OrderItemRead]

    model_config = {"from_attributes": True}


class OrderCreate(OrderBase):
    delivery_address: DeliveryAddressAdd
