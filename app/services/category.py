from typing import Annotated
from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.helpers.category import get_category_by_id
from app.validation.request import validate_non_empty_body
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def create_category_service(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Сервис для создания категории

    Args:
        data (CategoryCreate): Данные для создания категории
        session (AsyncSession, optional): Асинхронная сессия БД. Defaults to Depends(get_async_session).

    Returns:
        Созданная категория
    """
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


async def update_category_service(
    category_id: Annotated[int, Path(title="ID категории", ge=1)],
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Сервис для обновление данных категории

    Args:
        data (ProductUpdate): Данные для обновления категории
        category_id (Annotated[int, Path, optional): ID категории. Defaults to "ID товара", ge=1)].
        session (AsyncSession, optional): Асинхронная сессия БД. Defaults to Depends(get_async_session).

    Returns:
        Обновленная категория
    """
    try:
        update_data = validate_non_empty_body(data)

        category = await get_category_by_id(
            category_id=category_id,
            session=session,
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


async def delete_category_service(
    category_id: Annotated[int, Path(ge=1)],
    session: AsyncSession = Depends(get_async_session),
):
    """Сервис для удаления категории

    Args:
        category_id (Annotated[int, Path, optional): ID категории. Defaults to 1)].
        session (AsyncSession, optional): Асинхронная сессия БД. Defaults to Depends(get_async_session).
    """
    try:
        category = await get_category_by_id(
            category_id=category_id,
            session=session,
        )

        await session.delete(category)
        await session.commit()

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла внутренняя ошибка сервера",
        )
