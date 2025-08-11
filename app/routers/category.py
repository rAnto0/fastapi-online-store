from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.models.category import Category
from app.schemas.category import CategoryRead, CategoryCreate, CategoryUpdate


router = APIRouter(prefix="/category", tags=["Категории"])


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
    responses={
        404: {"description": "Категория не найдена"},
    },
)
async def get_category(
    category_id: Annotated[int, Path(title="ID категории", ge=1)],
    session: AsyncSession = Depends(get_async_session),
):
    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Категория не найдена"
        )

    return category


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryRead,
    summary="Создать категорию",
)
async def create_category(
    data: CategoryCreate, session: AsyncSession = Depends(get_async_session)
):
    try:
        category = Category(**data.model_dump(exclude_unset=True))

        session.add(category)
        await session.commit()
        await session.refresh(category)

        return category

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла ошибка при создании категории",
        )


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Обновить категорию по ID",
    responses={
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def update_category(
    category_id: Annotated[int, Path(title="ID категории", ge=1)],
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пустое тело запроса",
            )
        category = await session.get(Category, category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
            )

        for key, value in update_data.items():
            setattr(category, key, value)

        await session.commit()
        await session.refresh(category)

        return category

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла внутренняя ошибка сервера",
        )


@router.delete(
    "/{category_id}",
    summary="Удалить категорию по ID",
)
async def delete_category(
    category_id: Annotated[int, Path(ge=1)],
    session: AsyncSession = Depends(get_async_session),
):
    try:
        category = await session.get(Category, category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
            )

        await session.delete(category)
        await session.commit()

        return {"msg": "Категория успешна удалёна"}

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла внутренняя ошибка сервера",
        )
