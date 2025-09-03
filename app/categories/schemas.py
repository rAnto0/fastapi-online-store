from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: Annotated[
        str, Field(..., min_length=3, max_length=100, description="Название категории")
    ]
    description: Annotated[
        str | None, Field(max_length=500, description="Описание категории")
    ] = None

    model_config = {"str_strip_whitespace": True}


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryUpdate(BaseModel):
    name: Annotated[
        str | None, Field(min_length=3, max_length=100, description="Название категории")
    ] = None
    description: Annotated[
        str | None, Field(max_length=500, description="Описание категории")
    ] = None

    model_config = {"str_strip_whitespace": True}
