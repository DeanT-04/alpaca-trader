.PHONY: setup test lint format clean

setup:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

lint:
	ruff check .
	mypy .

format:
	ruff check --fix .
	black .

clean:
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
