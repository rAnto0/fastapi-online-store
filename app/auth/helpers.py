from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_jwt
from app.users.models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_token_payload(
    token: str = Depends(oauth2_scheme),
) -> dict[str, Any]:
    """
    Получает полезную нагрузку из JWT-токена.

    Args:
        token: JWT-токен из заголовка Authorization

    Returns:
        dict: Полезная нагрузка токена

    Raises:
        HTTPException: Если токен недействителен или истек
    """
    try:
        payload: dict[str, Any] = decode_jwt(token)
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_from_sub(
    payload: dict[str, Any],
    session: AsyncSession,
) -> User:
    """
    Получает пользователя из БД на основе sub (subject) из JWT-токена.

    Args:
        payload: Полезная нагрузка JWT-токена
        session: Асинхронная сессия БД

    Returns:
        User: Найденный пользователь

    Raises:
        HTTPException: Если пользователь не найден
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Получаем пользователя из БД
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user
