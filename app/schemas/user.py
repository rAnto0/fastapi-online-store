from typing import Annotated
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    username: Annotated[
        str, Field(..., min_length=3, max_length=50, description="Никнейм пользователя")
    ]
    email: Annotated[
        EmailStr | None, Field(..., max_length=50, description="Email пользователя")
    ] = None

    model_config = {"str_strip_whitespace": True}


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(UserBase):
    password: Annotated[
        str, Field(..., min_length=3, max_length=50, description="Пароль пользователя")
    ]


class UserLogin(UserBase):
    id: int
    password: Annotated[
        str, Field(..., min_length=3, max_length=50, description="Пароль пользователя")
    ]
