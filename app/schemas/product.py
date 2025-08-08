from typing import Annotated
from datetime import datetime
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    title: Annotated[
        str, Field(..., min_length=3, max_length=100, description="Название товара")
    ]
    description: Annotated[
        str | None, Field(max_length=500, description="Описание товара")
    ] = None
    price: Annotated[float, Field(..., gt=0, description="Цена товара")]


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    created_at: datetime
