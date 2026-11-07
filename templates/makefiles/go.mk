# Standard targets for a Go project. See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Download modules and tidy go.mod
	go mod download
	go mod tidy

format: ## Format the code
	gofmt -w .

lint: ## Vet and lint without changing files
	test -z "$$(gofmt -l .)"
	go vet ./...
	golangci-lint run
	govulncheck ./...

test: ## Run tests with the race detector
	go test -race ./...

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build the binary
	go build -o bin/app ./cmd/app

run: ## Run locally
	go run ./cmd/app

docker-build: ## Build the container image
	docker build -t app:local .

clean: ## Remove build output
	rm -rf bin
