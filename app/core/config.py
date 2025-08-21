from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel

from pathlib import Path


BASE_DIR = Path(__file__).parent.parent


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    DATABASE_SYNC_URL: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 0
    AUTH_JWT_KEYS: AuthJWT = AuthJWT()

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
