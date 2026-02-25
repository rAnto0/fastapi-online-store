# FastAPI Online Store

Бэкенд интернет‑магазина на **FastAPI** с асинхронным доступом к БД через **SQLAlchemy 2.0**, миграциями через **Alembic** и тестами на **pytest**.

## Что реализовано

- Аутентификация и регистрация пользователей (JWT access/refresh).
- Роли пользователей (обычный пользователь / администратор).
- Каталог товаров и категорий.
- Корзина пользователя.
- Оформление заказов и управление статусами заказа.
- Миграции базы данных.
- Набор интеграционных API‑тестов.

## Технологии

- Python 3.10+
- FastAPI
- SQLAlchemy 2.0 (async)
- Alembic
- PostgreSQL (основная и тестовая БД)
- Pytest + HTTPX

## Структура проекта

```text
app/
  auth/          # регистрация, логин, refresh, проверки токенов
  users/         # модель пользователя, схемы, валидации
  products/      # товары
  categories/    # категории
  cart/          # корзина
  orders/        # заказы и адрес доставки
  core/          # конфиг, безопасность, подключение к БД
  models/        # централизованный импорт моделей для SQLAlchemy/Alembic
alembic/         # миграции
tests/           # API-тесты и фикстуры
```

## Быстрый старт

### 1) Клонирование и установка зависимостей

```bash
git clone <repo-url>
cd fastapi-online-store
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/name-db
DATABASE_SYNC_URL=postgresql+psycopg2://user:pass@localhost:5432/name-db
DATABASE_TEST_URL=postgresql+asyncpg://user:pass@localhost:5432/name-db-test

SECRET_KEY=change-me
ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
```

> В проекте используется `RS256`, поэтому нужны RSA‑ключи:
>
> - `app/certs/jwt-private.pem`
> - `app/certs/jwt-public.pem`

Пример генерации ключей:

```bash
mkdir -p app/certs
openssl genrsa -out app/certs/jwt-private.pem 2048
openssl rsa -in app/certs/jwt-private.pem -pubout -out app/certs/jwt-public.pem
```

### 3) Применение миграций

```bash
alembic upgrade head
```

### 4) Запуск приложения

```bash
uvicorn app.main:app --reload
```

После запуска:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Основные эндпоинты

- `POST /auth/register` — регистрация
- `POST /auth/login` — логин
- `POST /auth/refresh` — обновление токенов
- `GET /me` — данные текущего пользователя
- `GET/POST/PATCH/DELETE /products/...` — товары
- `GET/POST/PATCH/DELETE /category/...` — категории
- `GET/POST/PATCH/DELETE /cart/...` — корзина
- `GET/POST/PATCH /orders/...` — заказы и статусы

## Тесты

```bash
pytest
```

Для запуска тестов нужен корректный `DATABASE_TEST_URL` в `.env`.
