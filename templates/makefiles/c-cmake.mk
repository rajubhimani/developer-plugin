# Standard targets for a C project built with CMake presets. See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Configure the debug preset
	cmake --preset debug

format: ## Format the code
	clang-format -i $$(git ls-files '*.c' '*.h')

lint: ## Format check and clang-tidy without changing files
	clang-format --dry-run --Werror $$(git ls-files '*.c' '*.h')
	clang-tidy -p build/debug $$(git ls-files '*.c')

test: ## Build and run the tests with sanitizers
	cmake --preset asan
	cmake --build --preset asan
	ctest --preset asan

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build the release preset
	cmake --preset release
	cmake --build --preset release

run: ## Run the program (executable projects)
	./build/release/{{name}}

docker-build: ## Build the container image
	docker build -t {{name}}:local .

clean: ## Remove build output
	rm -rf build
