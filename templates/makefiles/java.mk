# Standard targets for a Java project (Gradle wrapper). See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Resolve dependencies
	./gradlew dependencies

format: ## Format the code
	./gradlew spotlessApply

lint: ## Static analysis without changing files
	./gradlew spotlessCheck check -x test

test: ## Run unit tests
	./gradlew test

check: align ## Gate before reporting work done (analysis and tests)
	./gradlew check

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build the artifact
	./gradlew build

run: ## Run the application
	./gradlew run

docker-build: ## Build the container image
	docker build -t app:local .

clean: ## Remove build output
	./gradlew clean
