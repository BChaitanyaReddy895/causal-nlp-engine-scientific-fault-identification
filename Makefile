.PHONY: help setup dev run test lint format clean docker-build docker-up docker-down docs

help:
	@echo "Causal-NLP Engine - Available Commands"
	@echo "======================================"
	@echo "make setup          - Install dependencies and setup environment"
	@echo "make dev            - Run Flask development server locally"
	@echo "make run            - Run the full application with docker-compose"
	@echo "make test           - Run pytest test suite"
	@echo "make lint           - Run linters (flake8, mypy)"
	@echo "make format         - Format code with black and isort"
	@echo "make clean          - Remove cache files and built artifacts"
	@echo "make docker-build   - Build Docker images"
	@echo "make docker-up      - Start containers with docker-compose"
	@echo "make docker-down    - Stop containers"
	@echo "make docs           - Build documentation"
	@echo "make db-init        - Initialize database"

setup:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm
	mkdir -p data/{raw,processed} models/{graph_model,extractors}

dev:
	export FLASK_ENV=development; \
	export FLASK_APP=backend/app.py; \
	flask run --host 0.0.0.0 --port 5000

run:
	docker-compose up -d
	@echo "Application started!"
	@echo "Backend: http://localhost:5000"
	@echo "Frontend: http://localhost:3000"

test:
	pytest tests/ -v --cov=backend --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 backend/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	mypy backend/ --ignore-missing-imports

format:
	black backend/ tests/ scripts/
	isort backend/ tests/ scripts/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage
	rm -rf build/ dist/ *.egg-info

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Services running:"
	docker-compose ps

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

db-init:
	flask db init
	flask db migrate -m "Initial migration"
	flask db upgrade

install-reqs:
	pip install --upgrade pip
	pip install -r requirements.txt

.DEFAULT_GOAL := help
