# Standard targets for a Python monorepo (uv workspace). See the project-make skill.
.PHONY: help install format lint test check check-env align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Install every member into one environment from uv.lock
	uv sync --all-packages

format: ## Format the code
	uv run ruff format .

lint: ## Lint and type-check every member without changing files
	uv run ruff format --check .
	uv run ruff check .
	uv run pyright

test: ## Run every member's tests
	uv run pytest

check: align check-env lint test ## Gate before reporting work done

check-env: ## Each app's settings, .env.example and cluster config name the same variables
	@for d in apps/*/; do python3 scripts/check_env.py --root $$d || exit 1; done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build every member's wheel and source archive
	uv build --all-packages

run: ## Run one member: make run PKG=<member> CMD="<command>"
	@test -n "$(PKG)" -a -n "$(CMD)" || { echo 'usage: make run PKG=<member> CMD="<command>"'; exit 1; }
	uv run --package $(PKG) $(CMD)

docker-build: ## Build a member's image: make docker-build PKG=<member>
	@test -n "$(PKG)" || { echo "usage: make docker-build PKG=<member>"; exit 1; }
	docker build -f apps/$(PKG)/Dockerfile -t $(PKG):local .

clean: ## Remove build output and caches
	rm -rf dist build .pytest_cache .ruff_cache .mypy_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
