#!/bin/bash
set -e

echo "Running Ruff check..."
uv run ruff check .

echo "Running Ruff format check..."
uv run ruff format --check .

echo "Running Ty check..."
uv run ty check .

echo "All checks passed!"
