from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Category


async def get_category_by_id(category_id: int, session: AsyncSession):
    """
    Фукнция для получения категории по ID.
    """
    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена",
        )

    return category
