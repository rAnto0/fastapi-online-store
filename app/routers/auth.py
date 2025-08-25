from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.services.auth import validate_auth_user, get_current_auth_user_for_refresh
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, TokenInfo, RefreshRequest


router = APIRouter(
    prefix="/auth",
    tags=["Регистрация/Авторизация"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    summary="Регистрация пользователя",
)
async def register(
    data: UserCreate, session: AsyncSession = Depends(get_async_session)
):
    # Проверяем, нет ли пользователя с таким email или username
    result = await session.execute(
        select(User).where(
            (User.email == data.email) | (User.username == data.username)
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или username уже существует",
        )

    hashed_password: bytes = get_password_hash(data.password)
    new_user = User(
        username=data.username, email=data.email, hashed_password=hashed_password
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Авторизация пользователя",
    response_model=TokenInfo,
)
async def login(
    user: UserRead = Depends(validate_auth_user),
):
    access_token = create_access_token(user=user)
    refresh_token = create_refresh_token(user=user)

    return TokenInfo(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Обновление access токена по resresh токену",
    response_model=TokenInfo,
)
async def refresh(user: UserRead = Depends(get_current_auth_user_for_refresh)):
    access_token = create_access_token(user=user)
    refresh_token = create_refresh_token(user=user)

    return TokenInfo(access_token=access_token, refresh_token=refresh_token)
