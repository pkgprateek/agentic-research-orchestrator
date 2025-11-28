#!/bin/bash
set -e

echo "Running Ruff (Linting)..."
ruff check src/ tests/

echo "Running Mypy (Type Checking)..."
mypy src/

echo "Running Pytest (Unit & Integration)..."
pytest

echo "All tests passed!"
