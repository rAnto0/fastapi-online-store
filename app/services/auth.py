from typing import Annotated, Any

from fastapi import Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.auth import get_current_token_payload, get_user_from_sub
from app.helpers.user import get_user_by_username
from app.schemas.user import UserCreate, UserRead
from app.models.user import User
from app.core.database import get_async_session
from app.core.security import (
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
)
from app.validation.auth import validate_token_type
from app.validation.user import validate_user_admin, validate_user_unique


async def authenticate_user_service(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: AsyncSession = Depends(get_async_session),
):
    user = await get_user_by_username(
        username=username,
        session=session,
    )

    verify_password(
        plain_password=password,
        hashed_password=user.hashed_password,
    )

    return user


async def register_user_service(
    data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
):
    # Проверяем, нет ли пользователя с таким email и username
    await validate_user_unique(
        email=data.email,
        username=data.username,
        session=session,
    )

    hashed_password: bytes = get_password_hash(data.password)
    new_user = User(
        username=data.username, email=data.email, hashed_password=hashed_password
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


class UserGetterFromToken:
    def __init__(self, token_type: str) -> None:
        self.token_type = token_type

    async def __call__(
        self,
        payload: dict[str, Any] = Depends(get_current_token_payload),
        session: AsyncSession = Depends(get_async_session),
    ) -> User:
        """
        Получает пользователя на основе токена.

        Args:
            payload: Полезная нагрузка JWT-токена
            session: Асинхронная сессия БД

        Returns:
            User: Аутентифицированный пользователь
        """
        validate_token_type(
            payload=payload,
            token_type=self.token_type,
        )

        user = await get_user_from_sub(
            payload=payload,
            session=session,
        )

        return user


get_current_auth_user = UserGetterFromToken(ACCESS_TOKEN_TYPE)
get_current_refresh_user = UserGetterFromToken(REFRESH_TOKEN_TYPE)


async def validate_user_admin_service(
    user: UserRead = Depends(get_current_auth_user),
):
    validate_user_admin(user=user)
