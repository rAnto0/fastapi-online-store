from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
import jwt

from .config import settings
from app.users.schemas import UserRead


TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_jwt(
    token_type: str,
    token_data: dict,
    private_key: str = settings.AUTH_JWT_KEYS.private_key_path.read_text(),
    algorithm: str = settings.ALGORITHM,
    expires_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    expires_delta: timedelta | None = None,
):
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=expires_minutes))

    jwt_payload = {
        TOKEN_TYPE_FIELD: token_type,
        "exp": expire,
        "iat": now,
    }
    jwt_payload.update(token_data)

    return jwt.encode(jwt_payload, private_key, algorithm=algorithm)


def create_access_token(
    user: UserRead,
):
    jwt_payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
    }

    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def create_refresh_token(
    user: UserRead,
):
    jwt_payload = {"sub": str(user.id)}

    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_jwt(
    token: str | bytes,
    public_key: str = settings.AUTH_JWT_KEYS.public_key_path.read_text(),
    algorithm: str = settings.ALGORITHM,
):
    decoded = jwt.decode(token, public_key, algorithms=[algorithm])

    return decoded


def get_password_hash(password: str) -> bytes:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)


def verify_password(plain_password: str, hashed_password: bytes) -> None:
    if bcrypt.checkpw(plain_password.encode(), hashed_password):
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Неверный пароль",
    )
