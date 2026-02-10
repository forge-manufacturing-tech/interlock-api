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

## Environment Variables

The project uses `.env` files for configuration. 

- `.env`: Local development secrets (e.g., your personal API keys). **DO NOT COMMIT**.
- `.env.prod`: Production secrets used for deployment. **DO NOT COMMIT**.
- `.env.reference`: Example environment file. Update if new variables are added.

To start the API with local variables:
```bash
./apps/api/start.sh
```

To start the API with production variables (for testing):
```bash
./apps/api/start.sh ./.env.prod
```
