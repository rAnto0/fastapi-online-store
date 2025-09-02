from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from app.schemas.product import ProductRead


class CartBase(BaseModel):
    product_id: Annotated[int, Field(..., ge=1, description="ID товара")]
    quantity: Annotated[int, Field(..., ge=1, le=999, description="Количество товара")]


class CartAddProduct(CartBase):
    pass


class CartItemRead(BaseModel):
    id: int
    cart_id: int
    product_id: int
    product: ProductRead
    quantity: int

    @computed_field
    def total_price(self) -> float:
        """Общая стоимость позиции (quantity * product.price)"""
        return round(self.quantity * self.product.price, 2)

    model_config = {"from_attributes": True}


class CartItemQuantityUpdate(BaseModel):
    quantity: Annotated[int, Field(ge=0, le=999, description="Количество товара")]
