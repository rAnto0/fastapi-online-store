from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


def create_access_token(
    payload: dict,
    private_key: str = settings.AUTH_JWT_KEYS.private_key_path.read_text(),
    algorithm: str = settings.ALGORITHM,
    expires_delta: timedelta | None = None,
):
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update(exp=expire, iat=now)

    encoded = jwt.encode(to_encode, private_key, algorithm=algorithm)

    return encoded


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


def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password)
