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
    is_admin: bool

    model_config = {"from_attributes": True}


class UserCreate(UserBase):
    password: Annotated[
        str, Field(..., min_length=3, max_length=50, description="Пароль пользователя")
    ]


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
