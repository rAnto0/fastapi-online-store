from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserRead


async def validate_email_unique(
    email: EmailStr,
    session: AsyncSession,
    exclude_user_id: int | None = None,
) -> None:
    """
    Проверяет уникальность email пользователя.
    """
    query = select(User).where(User.email == email)
    if exclude_user_id:
        query = query.where(User.id != exclude_user_id)

    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )


async def validate_username_unique(
    username: str,
    session: AsyncSession,
    exclude_user_id: int | None = None,
) -> None:
    """
    Проверяет уникальность username пользователя.
    """
    query = select(User).where(User.username == username)
    if exclude_user_id:
        query = query.where(User.id != exclude_user_id)

    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким username уже существует",
        )


async def validate_user_unique(
    session: AsyncSession,
    email: EmailStr | None = None,
    username: str | None = None,
    exclude_user_id: int | None = None,
) -> None:
    """
    Проверяет уникальность email и username пользователя.
    """
    if email is None and username is None:
        return

    if email:
        await validate_email_unique(email, session, exclude_user_id)
    if username:
        await validate_username_unique(username, session, exclude_user_id)


def validate_user_admin(
    user: UserRead,
) -> None:
    """
    Проверяет пользователь админ или нет.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции",
        )
