# Standard targets for a Node.js or TypeScript project. See the project-make skill.
# Assumes the package.json scripts named lint, typecheck, test and build exist.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Install from the lock file
	npm ci

format: ## Format the code
	npx prettier --write .

lint: ## Lint and type-check without changing files
	npm run lint
	npm run typecheck

test: ## Run unit and component tests
	npm run test

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build the app
	npm run build

run: ## Start the dev server
	npm run dev

docker-build: ## Build the container image
	docker build -t app:local .

clean: ## Remove build output and dependencies
	rm -rf dist node_modules
