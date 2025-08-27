from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .core.database import get_async_session
from .routers import product, category, auth
from .schemas.user import UserRead
from .services.auth import get_current_auth_user

app = FastAPI(title="Shop API")
app.include_router(product.router)
app.include_router(category.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Shop API"}


@app.get("/db-test")
async def db_test(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(text("SELECT 1"))
    return {"db_status": result.scalar()}


@app.get("/me")
async def auth_user_check_self_info(user: UserRead = Depends(get_current_auth_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "дата создания": user.created_at,
    }
