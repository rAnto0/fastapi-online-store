from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel


def validate_non_empty_body(
    request_data: BaseModel,
    error_detail: str = "Пустое тело запроса",
) -> dict[str, Any]:
    """Проверка на пустое тело запроса

    Args:
        request_data (BaseModel): Данные
        error_detail (str, optional): Описание ошибки. Defaults to "Пустое тело запроса".

    Returns:
        dict[str, Any]: Словарь с данными
    """
    data = request_data.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail,
        )

    return data
