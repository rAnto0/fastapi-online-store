from logging.config import fileConfig
import os
from dotenv import load_dotenv
import sys
import importlib

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

load_dotenv()  # Загружаем .env файл

# Путь до app/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Импортируем Base из database.py
from app.core.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Получаем URL из .env или переменных окружения
db_url = os.getenv("DATABASE_SYNC_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Автоматически находим все приложения в папке app
apps_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../app"))
exclude_dirs = ["__pycache__", "certs", "validations", "core"]
apps = []

for item in os.listdir(apps_path):
    if item in exclude_dirs or item.startswith("."):
        continue
    item_path = os.path.join(apps_path, item)
    if (
        os.path.isdir(item_path)
        and not item.startswith("__")
        and not item.startswith(".")
    ):
        # Проверяем, есть ли в папке models.py
        if os.path.exists(os.path.join(item_path, "models.py")):
            apps.append(item)
            print(f"Found app with models: {item}")

# Затем импортируем модели из найденных приложений
for app_name in apps:
    try:
        importlib.import_module(f"app.{app_name}.models")
        print(f"Successfully imported models from {app_name}")
    except Exception as e:
        print(f"Error importing models from {app_name}: {e}")

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
