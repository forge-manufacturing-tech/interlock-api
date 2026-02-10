# Gemini Instructions

When working on this codebase, always ensure that your changes pass the linting checks.
Use the provided `lint.sh` script to verify your code.

```bash
./lint.sh
```

This script runs:
- Ruff check (linting)
- Ruff format check (formatting)
- Ty check (type checking)

If any check fails, fix the errors before submitting your changes.
To auto-format your code, run:
```bash
uv run ruff format .
```
