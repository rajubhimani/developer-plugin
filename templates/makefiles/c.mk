# Standard targets for a C project (CMake). See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Configure the debug build
	cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

format: ## Format the code
	clang-format -i $$(git ls-files '*.c' '*.h')

lint: ## Static analysis without changing files
	clang-tidy -p build $$(git ls-files '*.c')

test: ## Build with sanitizers and run tests
	cmake --build build
	ctest --test-dir build --output-on-failure

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build the release binary
	cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release
	cmake --build build-release

run: ## Run the program
	./build/app

docker-build: ## Build the container image
	docker build -t app:local .

clean: ## Remove build output
	rm -rf build build-release
