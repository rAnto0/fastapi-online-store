from typing import Annotated

from fastapi import Form, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.database import get_async_session
from app.core.security import verify_password, decode_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def validate_auth_user(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    session: AsyncSession = Depends(get_async_session),
):
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль"
    )

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise unauthed_exc

    if not verify_password(
        plain_password=password, hashed_password=user.hashed_password
    ):
        raise unauthed_exc

    return user


async def get_current_auth_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_jwt(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Получаем пользователя из БД
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user
