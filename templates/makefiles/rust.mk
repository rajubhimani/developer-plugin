# Standard targets for a Rust project. See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Fetch dependencies from Cargo.lock
	cargo fetch --locked

format: ## Format the code
	cargo fmt --all

lint: ## Lint and policy checks without changing files
	cargo fmt --all -- --check
	cargo clippy --all-targets --all-features -- -D warnings
	cargo deny check

test: ## Run tests
	cargo test --workspace --all-features

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build the release binary
	cargo build --release

run: ## Run locally
	cargo run

docker-build: ## Build the container image
	docker build -t app:local .

clean: ## Remove build output
	cargo clean
