.PHONY: build up down logs shell doctor test lint lock

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f ball-cv

shell:
	docker compose exec ball-cv bash

doctor:
	docker compose exec ball-cv python -m ball_cv doctor

test:
	docker compose exec ball-cv pytest

lint:
	docker compose exec ball-cv ruff check .

lock:
	docker compose exec ball-cv uv lock
