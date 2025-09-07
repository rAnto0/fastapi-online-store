from fastapi import HTTPException, status

from .models import Product


def validate_product_in_stock(
    product: Product,
    quantity: int | None = None,
) -> None:
    """
    Проверяет, есть ли товар в наличии.

    Args:
        product: Экземпляр таблицы Product
        quantity: Запрашиваемое количество

    Raises:
        HTTPException: Если товара нет на складе или запрашиваемое количество больше чем есть на складе
    """
    if product.stock_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Товар отсутствует на складе",
        )

    if quantity and ((product.stock_quantity - product.reserved) < quantity):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Запрашиваемое количество превышает доступное",
                "available": product.stock_quantity - product.reserved,
                "requested": quantity,
            },
        )
