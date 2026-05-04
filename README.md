# FastAPI Online Store

Бэкенд интернет-магазина на **FastAPI** с асинхронным доступом к БД через **SQLAlchemy 2.0**, миграциями через **Alembic** и тестами на **pytest**. Весь рабочий процесс построен на **Docker** и **Make**.

## Что реализовано

- Аутентификация и регистрация пользователей (JWT access/refresh, RS256)
- Роли пользователей (обычный пользователь / администратор)
- Каталог товаров и категорий с фильтрацией, сортировкой и пагинацией
- Корзина пользователя с резервированием товаров
- Оформление заказов, управление статусами, адрес доставки
- Миграции базы данных через Alembic
- Интеграционные API-тесты с покрытием ≥ 80%
- CI через GitHub Actions (lint, format-check, tests)

## Технологии

- Python 3.12+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) + asyncpg
- Alembic
- PostgreSQL 16
- PyJWT (RS256)
- bcrypt
- Pytest + HTTPX
- Docker + Docker Compose

## Структура проекта

```text
app/
  auth/          # регистрация, логин, refresh, проверки токенов
  users/         # модель пользователя, схемы, валидации
  products/      # товары, резервирование остатков
  categories/    # категории
  cart/          # корзина
  orders/        # заказы и адрес доставки
  core/          # конфиг, безопасность, подключение к БД
  models/        # централизованный импорт моделей для SQLAlchemy/Alembic
  validations/   # общие валидаторы запросов
  certs/         # RSA-ключи для JWT (генерируются локально, не коммитятся)
alembic/         # миграции
scripts/         # вспомогательные скрипты (env, JWT-ключи, seed)
tests/           # API-тесты и фикстуры
```

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repo-url>
cd fastapi-online-store
```

### 2. Создание `.env` файлов

Скрипт автоматически создаёт `.env.dev` и `.env.prod` на основе `.env.example`:

```bash
make env-init
```

При необходимости отредактируйте `.env.dev` вручную.

### 3. Генерация RSA-ключей для JWT

```bash
make keys-init
```

Ключи сохраняются в `app/certs/jwt-private.pem` и `app/certs/jwt-public.pem`. Для пересоздания существующих ключей:

```bash
./scripts/init-jwt-keys.sh --force
```

### 4. Запуск приложения (dev)

```bash
make run-dev
```

Поднимает PostgreSQL и приложение с hot-reload. После запуска:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 5. Применение миграций

```bash
make migrate
```

## Make-команды

### Dev-окружение

| Команда | Описание |
|---|---|
| `make run-dev` | Запустить все сервисы в фоне |
| `make down-dev` | Остановить все сервисы |
| `make down-dev ARGS="-v"` | Остановить и удалить volumes |
| `make build-dev` | Пересобрать Docker-образы |
| `make logs-dev SERVICE=app` | Посмотреть логи приложения |
| `make shell-service-dev SERVICE=app` | Открыть shell сервиса в контейнере |
| `make migrate` | Применить миграции Alembic |
| `make seed` | Загрузить тестовые данные |

### Качество кода

| Команда | Описание |
|---|---|
| `make lint` | Проверить стиль (ruff check) |
| `make lint-fix` | Исправить ошибки автоматически |
| `make format` | Отформатировать код (ruff format) |
| `make format-check` | Проверить форматирование без изменений |
| `make check` | lint + format-check + test |

### Тесты

| Команда | Описание |
|---|---|
| `make test` | Запустить тесты (создаёт тестовую БД автоматически) |

Дополнительные аргументы pytest можно передать через переменную:

```bash
make test PYTEST_ARGS="-v -k test_auth"
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `DATABASE_URL` | Async-подключение к БД (asyncpg) |
| `DATABASE_SYNC_URL` | Sync-подключение к БД (psycopg2, для Alembic) |
| `DATABASE_TEST_URL` | Подключение к тестовой БД |
| `SECRET_KEY` | Секретный ключ (не используется при RS256, но обязателен) |
| `ALGORITHM` | Алгоритм JWT (по умолчанию `RS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access-токена в минутах |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh-токена в днях |

## Основные эндпоинты

### Авторизация
- `POST /auth/register` — регистрация
- `POST /auth/login` — логин (возвращает access + refresh токены)
- `POST /auth/refresh` — обновление токенов по refresh-токену
- `GET /me` — данные текущего пользователя

### Товары и категории
- `GET/POST/PATCH/DELETE /products/` — управление товарами
- `GET /products/?category_id=&title=&sort_price=asc` — фильтрация и поиск
- `GET/POST/PATCH/DELETE /category/` — управление категориями

### Корзина
- `GET /cart/` — получить корзину
- `POST /cart/add` — добавить товар
- `PATCH /cart/item/{product_id}` — изменить количество (0 — удалить)
- `DELETE /cart/item/{product_id}` — удалить товар
- `DELETE /cart/clear` — очистить корзину

### Заказы
- `GET /orders/` — все заказы пользователя
- `GET /orders/{order_id}` — заказ по ID
- `POST /orders/create` — создать заказ из корзины
- `PATCH /orders/{order_id}/cancel/` — отменить заказ
- `PATCH /orders/{order_id}/confirm/` — подтвердить (admin)
- `PATCH /orders/{order_id}/processing/` — начать сборку (admin)
- `PATCH /orders/{order_id}/shipped/` — отправить (admin)
- `PATCH /orders/{order_id}/delivered/` — доставлен (admin)

## CI (GitHub Actions)

При каждом push и pull request автоматически выполняются:

1. **Merge Conflict Check** — проверка отсутствия конфликтов слияния (только для PR)
2. **Tests** — lint, format-check и полный прогон тестов в Docker-окружении