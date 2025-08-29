from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.services.auth import (
    register_user_service,
    authenticate_user_service,
    get_current_refresh_user,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, TokenInfo
from app.validation.user import validate_user_unique


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
async def register(new_user: UserRead = Depends(register_user_service)):
    return new_user


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Авторизация пользователя",
    response_model=TokenInfo,
)
async def login(
    user: UserRead = Depends(authenticate_user_service),
):
    access_token = create_access_token(user=user)
    refresh_token = create_refresh_token(user=user)

    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Обновление access токена по resresh токену",
    response_model=TokenInfo,
)
async def refresh(user: UserRead = Depends(get_current_refresh_user)):
    access_token = create_access_token(user=user)
    refresh_token = create_refresh_token(user=user)

    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
    )
