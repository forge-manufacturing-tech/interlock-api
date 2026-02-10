# Agent Instructions

## Linting & Quality Checks

Before completing any task involving code changes, you MUST run the linting script to ensure code quality and correctness.

```bash
./lint.sh
```

This script validates:
1. **Linting** (Ruff)
2. **Formatting** (Ruff)
3. **Type Safety** (Ty)

## Fixing Issues

- If **formatting** fails, run: `uv run ruff format .`
- If **linting** fails, fix the reported errors manually or use `uv run ruff check --fix .` (use caution with auto-fix).
- If **type checking** fails, resolve the type errors. Do not suppress them unless absolutely necessary.
