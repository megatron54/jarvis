.PHONY: dev serve chat test lint format setup docker-up docker-down models

# Development
dev:
	uvicorn jarvis.main:app --host 0.0.0.0 --port 8080 --reload

serve:
	jarvis serve

chat:
	jarvis chat

# Testing
test:
	pytest tests/ -v --cov=jarvis

test-unit:
	pytest tests/unit -v

# Code quality
lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/

# Infrastructure
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# Models
models:
	bash scripts/download_models.sh

# Setup
setup:
	bash scripts/setup.sh
