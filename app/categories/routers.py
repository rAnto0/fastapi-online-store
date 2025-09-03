from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.auth.services import validate_user_admin_service
from .helpers import get_category_by_id
from .models import Category
from .schemas import CategoryRead
from .services import (
    create_category_service,
    delete_category_service,
    update_category_service,
)


router = APIRouter(prefix="/category", tags=["Категории"])


admin_deps = [Depends(validate_user_admin_service)]


@router.get(
    "/", response_model=list[CategoryRead], summary="Получить список всех категорий"
)
async def get_categories(
    session: AsyncSession = Depends(get_async_session),
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
):
    query = select(Category).order_by(Category.id).offset(offset).limit(limit)
    categories = await session.execute(query)

    return categories.scalars().all()


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Получить категорию по ID",
)
async def get_category(
    category_id: Annotated[int, Path(title="ID категории", ge=1)],
    session: AsyncSession = Depends(get_async_session),
):
    category = await get_category_by_id(
        category_id=category_id,
        session=session,
    )

    return category


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryRead,
    dependencies=admin_deps,
    summary="Создать категорию",
)
async def create_category(category: CategoryRead = Depends(create_category_service)):
    return category


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    dependencies=admin_deps,
    summary="Обновить категорию по ID",
)
async def update_category(category: CategoryRead = Depends(update_category_service)):
    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=admin_deps,
    summary="Удалить категорию по ID",
)
async def delete_category(_: None = Depends(delete_category_service)):
    return Response(status_code=status.HTTP_204_NO_CONTENT)
