.PHONY: dev up down migrate test lint fmt

dev:
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up --build

up:
	docker compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d --build

down:
	docker compose down

migrate:
	uv run alembic upgrade head

migrate-create:
	uv run alembic revision --autogenerate -m "$(name)"

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check app/ tests/

fmt:
	uv run ruff format app/ tests/
