.PHONY: install dev lint test run docker-build docker-run clean

# Install production dependencies
install:
	pip install .

# Install with dev dependencies
dev:
	pip install -e ".[dev]"

# Run linter
lint:
	ruff check bot/ tests/
	ruff format --check bot/ tests/

# Fix lint issues
lint-fix:
	ruff check --fix bot/ tests/
	ruff format bot/ tests/

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=bot --cov-report=term-missing

# Run locally
run:
	python -m bot

# Build Docker image
docker-build:
	docker build -t github-notifier-bot .

# Run Docker container
docker-run:
	docker run --rm -it \
		--env-file .env \
		-v $(PWD)/config.yaml:/app/config.yaml:ro \
		-p 8000:8000 \
		github-notifier-bot

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
