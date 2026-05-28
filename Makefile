PYTHON ?= python3

.PHONY: format format-check lint typecheck unit-tests tests test venv build
.DEFAULT_GOAL := help

format: ## Format source files with black
	uv run black cambium_cnmaestro tests

format-check: ## Check formatting with black
	uv run black --check --diff cambium_cnmaestro tests

lint: format-check ## Run flake8 lint checks
	uv run flake8 cambium_cnmaestro tests

typecheck: ## Run mypy type checks
	uv run mypy cambium_cnmaestro

unit-tests: ## Run unit tests
	uv run pytest

tests: lint typecheck unit-tests ## Run all tests

test: tests ## Alias for tests

build: ## Build sdist and wheel
	uv build

venv: ## Create venv and sync dev dependencies
	test -d .venv || uv venv
	uv sync --extra dev

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

