# ISA-Forge Makefile

.PHONY: help install install-dev test test-cov lint format type-check clean conda-env

help:
	@echo "ISA-Forge Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install package"
	@echo "  make install-dev      Install with dev dependencies"
	@echo "  make conda-env        Create conda environment"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make test-html        Run tests with HTML coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Auto-format code"
	@echo "  make type-check       Run type checking"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and cache"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

conda-env:
	conda env create -f environment.yml

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src/isaforge --cov-report=term-missing

test-html:
	pytest tests/ --cov=src/isaforge --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

type-check:
	mypy src/isaforge/ --ignore-missing-imports

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
