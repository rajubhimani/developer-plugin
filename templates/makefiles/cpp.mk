# Standard targets for a C++ project (CMake presets). See the project-make skill.
.PHONY: help install format lint test check align build run docker-build clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Configure the debug preset
	cmake --preset debug

format: ## Format the code
	clang-format -i $$(git ls-files '*.cpp' '*.hpp' '*.h')

lint: ## Format check and clang-tidy without changing files
	clang-format --dry-run --Werror $$(git ls-files '*.cpp' '*.hpp' '*.h')
	clang-tidy -p build/debug $$(git ls-files '*.cpp')

test: ## Build and run tests with sanitizers
	cmake --build --preset asan
	ctest --preset asan

check: align lint test ## Gate before reporting work done

align: ## Check the project follows the plugin guidelines (tests/alignment)
	python3 -m unittest discover -s tests/alignment -p 'test_*.py'

build: ## Build the release preset
	cmake --preset release
	cmake --build --preset release

run: ## Run the program
	./build/release/app

docker-build: ## Build the container image
	docker build -t app:local .

clean: ## Remove build output
	rm -rf build
