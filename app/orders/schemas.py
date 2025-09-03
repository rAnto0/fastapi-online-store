from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"  # Ожидает подтверждения
    CONFIRMED = "confirmed"  # Подтвержден
    PROCESSING = "processing"  # В обработке/сборке
    SHIPPED = "shipped"  # Отправлен
    DELIVERED = "delivered"  # Доставлен
    CANCELLED = "cancelled"  # Отменен
    REFUNDED = "refunded"  # Возвращен


class PaymentMethods(str, Enum):
    CARD = "card"  # оплата картой
    CASH = "cash"  # оплата наличными
