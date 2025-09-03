from enum import Enum
from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, Field


class PriceSort(str, Enum):
    asc = "asc"
    desc = "desc"


class ProductBase(BaseModel):
    title: Annotated[
        str, Field(..., min_length=3, max_length=100, description="Название товара")
    ]
    description: Annotated[
        str | None, Field(max_length=500, description="Описание товара")
    ] = None
    price: Annotated[float, Field(..., gt=0, description="Цена товара")]
    category_id: Annotated[int, Field(..., ge=1, description="ID категории")]
    stock_quantity: Annotated[
        int, Field(..., ge=0, le=999, description="Количество товара на складе")
    ]

    model_config = {"str_strip_whitespace": True}


class ProductCreate(ProductBase):
    pass


class CategoryInProduct(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    category: CategoryInProduct

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    title: Annotated[
        str | None, Field(min_length=3, max_length=100, description="Название товара")
    ] = None
    description: Annotated[
        str | None, Field(max_length=500, description="Описание товара")
    ] = None
    price: Annotated[float | None, Field(gt=0, description="Цена товара")] = None
    category_id: Annotated[int | None, Field(ge=1, description="ID категории")] = None
    stock_quantity: Annotated[
        int | None, Field(ge=0, le=999, description="Количество товара на складе")
    ] = None

    model_config = {"str_strip_whitespace": True}
