.PHONY: help build up down logs clean test seed migrate shell

help:
	@echo "Graph Navigator - Available Commands"
	@echo "===================================="
	@echo "build    - Build Docker containers"
	@echo "up       - Start all services"
	@echo "down     - Stop all services"
	@echo "logs     - View service logs"
	@echo "clean    - Remove containers and volumes"
	@echo "test     - Run tests"
	@echo "seed     - Seed the database"
	@echo "migrate  - Run database migrations"
	@echo "shell    - Open a shell in the API container"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

test:
	docker-compose run --rm api pytest -v

seed:
	docker-compose run --rm api python scripts/seed_database.py

migrate:
	docker-compose run --rm api alembic upgrade head

shell:
	docker-compose exec api /bin/bash
