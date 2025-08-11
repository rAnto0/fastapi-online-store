from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .core.database import get_async_session
from .routers import products, category

app = FastAPI(title="Shop API")
app.include_router(products.router)
app.include_router(category.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Shop API"}


@app.get("/db-test")
async def db_test(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(text("SELECT 1"))
    return {"db_status": result.scalar()}
