from fastapi import Depends
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from .factories import *
from .helpers import *
from app.main import app
from app.core.database import get_async_session, Base
from app.core.config import settings
from app.auth.services import validate_user_admin_service
from app.users.models import User


@pytest.fixture(scope="session")
def faker():
    import faker

    return faker.Faker()


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


@pytest.fixture
async def db_session(async_engine):
    # открываем connection и стартуем глобальную транзакцию
    async with async_engine.connect() as conn:
        trans = await conn.begin()  # outer transaction

        # фабрика сессий, привязанная к открытому connection
        async_session = async_sessionmaker(
            bind=conn, expire_on_commit=False, class_=AsyncSession
        )

        async with async_session() as session:
            # стартуем nested transaction (SAVEPOINT) для теста
            await session.begin_nested()

            # слушатель для автоматического восстановления nested savepoint после отката
            def _restart_savepoint(session_, transaction):
                # если вложенная транзакция закончилась (rollback/commit),
                # и сейчас мы не в nested транзакции — создаём новый savepoint
                if not session_.in_nested_transaction():
                    session_.begin_nested()

            event.listen(
                session.sync_session, "after_transaction_end", _restart_savepoint
            )

            try:
                yield session
            finally:
                # удаляем слушатель чтобы избежать побочных эффектов
                event.remove(
                    session.sync_session, "after_transaction_end", _restart_savepoint
                )

                # закрываем сессию и откатываем outer транзакцию
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
async def non_admin_user(user_factory):
    """Создает обычного пользователя (не admin)"""
    return await user_factory()


@pytest.fixture
async def admin_user(admin_user_factory):
    """Создает пользователя-администратора"""
    return await admin_user_factory()


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
