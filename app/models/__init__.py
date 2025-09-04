"""
Централизованный импорт моделей приложения.

Гарантирует, что все модули с моделями будут импортированы
одним вызовом: `import app.models`.
Нужно, чтобы SQLAlchemy корректно разрешал relationship("...") с
строковыми путями и чтобы Alembic видел все метаданные.
"""

from importlib import import_module

# Явный список папок в app/, в которых есть models.py
apps = [
    "users",
    "products",
    "cart",
    "categories",
    "orders",
]

for a in apps:
    try:
        import_module(f"app.{a}.models")
    except Exception as exc:
        raise
