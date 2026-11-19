# Standard targets for a TypeScript monorepo (pnpm workspace). See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Install every member from the lock file
	pnpm install --frozen-lockfile

format: ## Format the code
	pnpm -r --if-present format

lint: ## Type-check and lint every member
	pnpm -r --if-present typecheck
	pnpm -r --if-present lint

test: ## Run every member's tests
	pnpm -r --if-present test

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build every member
	pnpm -r --if-present build

run: ## Run one member: make run PKG=<member> CMD=<script>
	@test -n "$(PKG)" -a -n "$(CMD)" || { echo "usage: make run PKG=<member> CMD=<script>"; exit 1; }
	pnpm --filter $(PKG) run $(CMD)

docker-build: ## Build an app's image: make docker-build PKG=<app> (needs apps/<app>/Dockerfile)
	@test -n "$(PKG)" || { echo "usage: make docker-build PKG=<app>"; exit 1; }
	docker build -f apps/$(PKG)/Dockerfile -t $(PKG):local .

clean: ## Remove build output
	rm -rf apps/*/dist packages/*/dist node_modules apps/*/node_modules packages/*/node_modules
