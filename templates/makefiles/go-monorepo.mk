# Standard targets for a Go workspace (go.work). See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

MODULES := $(wildcard apps/* packages/*)

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Download every module's dependencies
	@for m in $(MODULES); do (cd $$m && go mod download) || exit 1; done

format: ## Format the code
	gofmt -w $(MODULES)

lint: ## Format check, vet, lint and vulnerability scan in every module
	@for m in $(MODULES); do echo "== $$m"; (cd $$m && test -z "$$(gofmt -l .)" && go vet ./... && golangci-lint run && govulncheck ./...) || exit 1; done

test: ## Run every module's tests with the race detector
	@for m in $(MODULES); do echo "== $$m"; (cd $$m && go test -race ./...) || exit 1; done

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build every module
	@for m in $(MODULES); do (cd $$m && go build ./...) || exit 1; done

run: ## Run one command: make run PKG=<member>
	@test -n "$(PKG)" || { echo "usage: make run PKG=<member>"; exit 1; }
	cd apps/$(PKG) && go run ./cmd/*

docker-build: ## Build an app's image: make docker-build PKG=<member> (needs apps/<member>/Dockerfile)
	@test -n "$(PKG)" || { echo "usage: make docker-build PKG=<member>"; exit 1; }
	docker build -f apps/$(PKG)/Dockerfile -t $(PKG):local .

clean: ## Remove build output
	rm -rf bin dist
