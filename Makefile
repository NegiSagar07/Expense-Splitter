# ==============================================================
# Makefile — Expense Splitter shortcuts
# ==============================================================
# Usage: make <target>
# Requires: docker, docker compose
# ==============================================================

.DEFAULT_GOAL := help
COMPOSE        := docker compose
BACKEND        := $(COMPOSE) exec backend

.PHONY: help up down build logs shell \
        migrate migrate-gen migrate-history \
        seed test lint

# ── Help ───────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Expense Splitter — available commands"
	@echo ""
	@echo "  make up              Start all services (build if needed)"
	@echo "  make down            Stop all services"
	@echo "  make down-v          Stop + wipe database volume"
	@echo "  make build           Rebuild images"
	@echo "  make logs            Tail all service logs"
	@echo "  make logs-backend    Tail backend logs only"
	@echo "  make logs-frontend   Tail frontend logs only"
	@echo "  make shell           Open a shell inside the backend container"
	@echo "  make psql            Open psql inside the db container"
	@echo ""
	@echo "  make migrate         Apply all pending Alembic migrations"
	@echo "  make migrate-gen m=<message>  Generate a new migration"
	@echo "  make migrate-history Show migration history"
	@echo "  make migrate-down    Downgrade one revision"
	@echo ""
	@echo "  make seed            Populate DB with development test data"
	@echo "  make test            Run the test suite"
	@echo "  make lint            Run ruff linter"
	@echo ""

# ── Docker Compose lifecycle ───────────────────────────────────
up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

logs-backend:
	$(COMPOSE) logs -f backend

logs-frontend:
	$(COMPOSE) logs -f frontend

shell:
	$(BACKEND) /bin/sh

psql:
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-expense_user} -d $${POSTGRES_DB:-expense_splitter_db}

# ── Alembic migrations ─────────────────────────────────────────
migrate:
	$(BACKEND) alembic upgrade head

# Usage: make migrate-gen m="add_invite_links"
migrate-gen:
	$(BACKEND) alembic revision --autogenerate -m "$(m)"

migrate-history:
	$(BACKEND) alembic history --verbose

migrate-down:
	$(BACKEND) alembic downgrade -1

# ── Development data ───────────────────────────────────────────
seed:
	$(BACKEND) python -m scripts.seed_dev_db

# ── Tests ──────────────────────────────────────────────────────
test:
	$(BACKEND) pytest -v --cov=app --cov-report=term-missing

# ── Lint ───────────────────────────────────────────────────────
lint:
	$(BACKEND) ruff check app/ tests/
