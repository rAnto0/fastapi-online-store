COMPOSE_DEV = docker compose --env-file .env.dev -f docker-compose.yaml -f docker-compose.dev.yaml
PYTEST_ARGS ?= -q --disable-warnings -r fE

.PHONY: run-dev down-dev build-dev logs-dev shell-service-dev test test-db env-init keys-init migrate seed-courses lint lint-fix format format-check check

# =======
# HELPERS
# =======
define ensure_db
	@echo "Ensuring test database $(1)..."
	@$(COMPOSE_DEV) exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$(1)';" | grep -q 1 || $(COMPOSE_DEV) exec -T postgres psql -U postgres -c "CREATE DATABASE $(1);"
endef

# ============
# DEV COMMANDS
# ============
run-dev:
	$(COMPOSE_DEV) up -d $(ARGS)

down-dev:
	$(COMPOSE_DEV) down $(ARGS)

build-dev:
	$(COMPOSE_DEV) build $(ARGS)

logs-dev:
	$(COMPOSE_DEV) logs $(SERVICE)

shell-service-dev:
	$(COMPOSE_DEV) exec -it $(SERVICE) sh -lc 'command -v bash >/dev/null 2>&1 && exec bash || exec sh'

# =======
# SCRIPTS
# =======
env-init:
	./scripts/init-env.sh

keys-init:
	./scripts/init-jwt-keys.sh

seed-courses:
	python3 scripts/seed_courses.py

migrate:
	$(COMPOSE_DEV) exec -T app uv run alembic -c alembic.ini upgrade head

# =============
# TEST COMMANDS
# =============
lint:
	@echo "Running ruff lint..."
	@$(COMPOSE_DEV) exec -T app uv run --extra dev ruff check .

lint-fix:
	@echo "Running ruff lint with fixes..."
	@$(COMPOSE_DEV) exec -T app uv run --extra dev ruff check . --fix

format:
	@echo "Running ruff format..."
	@$(COMPOSE_DEV) exec -T app uv run --extra dev ruff format .

format-check:
	@echo "Checking ruff format..."
	@$(COMPOSE_DEV) exec -T app uv run --extra dev ruff format --check .

check: lint format-check test

test: test-db
	@echo "Running tests..."
	@$(COMPOSE_DEV) exec -T app uv run pytest $(PYTEST_ARGS)

test-db:
	$(call ensure_db,postgres_db_test)