from fastapi import APIRouter, Depends, status

from app.core.security import (
    create_access_token,
    create_refresh_token,
)
from app.users.schemas import UserRead, TokenInfo
from .services import (
    register_user_service,
    authenticate_user_service,
    get_current_refresh_user,
)


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
