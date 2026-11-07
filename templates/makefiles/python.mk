# Standard targets for a Python project (uv). See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Install dependencies from uv.lock
	uv sync

format: ## Format the code
	uv run ruff format .

lint: ## Lint and type-check without changing files
	uv run ruff format --check .
	uv run ruff check .
	uv run pyright

test: ## Run tests
	uv run pytest

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build the package
	uv build

run: ## Run locally (edit the module name)
	uv run python -m app

docker-build: ## Build the container image
	docker build -t app:local .

clean: ## Remove build output and caches
	rm -rf dist build .pytest_cache .ruff_cache .mypy_cache
