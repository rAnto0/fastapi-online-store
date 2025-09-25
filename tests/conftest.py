from fastapi import Depends
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from .factories import *
from .helpers import *
from app.main import app
from app.core.database import get_async_session, Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.auth.services import validate_user_admin_service
from app.users.models import User


@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        settings.DATABASE_TEST_URL, echo=False, poolclass=NullPool
    )
    # создаём схему один раз
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


# Для каждого теста - отдельное соединение и транзакция
@pytest.fixture
async def db_session(async_engine):
    # открываем connection и стартуем транзакцию
    async with async_engine.connect() as conn:
        trans = await conn.begin()  # глобальная транзакция
        # фабрика сессий, привязанная к открытому connection
        async_session = async_sessionmaker(
            bind=conn, expire_on_commit=False, class_=AsyncSession
        )

        async with async_session() as session:
            try:
                yield session
            finally:
                # откатим изменения, сделанные в тесте
                await session.close()
                await trans.rollback()


@pytest.fixture
async def override_get_db(db_session):
    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture
async def async_client(override_get_db):
    app.dependency_overrides[get_async_session] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
async def override_admin_dependency():
    async def _fake_admin():
        return True

    app.dependency_overrides[validate_user_admin_service] = _fake_admin
    yield
    app.dependency_overrides.pop(validate_user_admin_service, None)


@pytest.fixture
async def non_admin_user(db_session):
    """
    Создаёт в тестовой БД обычного пользователя (не admin).
    """
    password = "TestUser010203"
    user = User(
        username="TestUser",
        email="TestUser@example.test",
        hashed_password=get_password_hash(password),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def auth_client_non_admin(async_client, non_admin_user):
    """
    Переопределяем dependency, который возвращает current user, на нашу фикстуру.
    """
    try:
        from app.auth.services import get_current_auth_user
    except Exception:
        get_current_auth_user = None

    async def _override_get_current_user(
        session: AsyncSession = Depends(get_async_session),
    ):
        result = await session.execute(select(User).where(User.id == non_admin_user.id))
        user = result.scalars().first()
        return user

    if get_current_auth_user:
        app.dependency_overrides[get_current_auth_user] = _override_get_current_user

    yield async_client

    if get_current_auth_user:
        app.dependency_overrides.pop(get_current_auth_user, None)
