from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .core.database import get_async_session
from .products import routers as products_router
from .categories import routers as categories_router
from .auth import routers as auth_router
from .cart import routers as cart_router
from .orders import routers as order_router
from .users.schemas import UserRead
from .auth.services import get_current_auth_user


app = FastAPI(title="Shop API")
app.include_router(products_router.router)
app.include_router(categories_router.router)
app.include_router(auth_router.router)
app.include_router(cart_router.router)
app.include_router(order_router.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Shop API"}


@app.get("/db-test")
async def db_test(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(text("SELECT 1"))
    return {"db_status": result.scalar()}


@app.get("/me")
async def auth_user_check_self_info(user: UserRead = Depends(get_current_auth_user)):
    user_info_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "дата создания": user.created_at,
    }
    if user.is_admin:
        user_info_dict.update({"admin": True})

    return user_info_dict
