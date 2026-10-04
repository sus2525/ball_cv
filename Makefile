.PHONY: build up down logs shell doctor test lint lock track

build:
	docker compose build

up:
	docker compose up -d --build --wait --wait-timeout 300

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

track:
	@test -n "$(VIDEO)" || (echo 'Usage: make track VIDEO=/data/videos/match.mp4 [ARGS="--class-id 0"]' >&2; exit 2)
	docker compose exec ball-cv python -m ball_cv track-video "$(VIDEO)" $(ARGS)
