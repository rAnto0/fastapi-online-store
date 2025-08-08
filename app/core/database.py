from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from collections.abc import AsyncGenerator
from .config import settings

# Создаём движок SQLAlchemy
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Фабрика сессий
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


# Dependency для получения сессии
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
