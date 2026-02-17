# Interlock API

This is the API for the Interlock monorepo. It is a FastAPI application that provides a REST API for the Interlock system.

## Project Structure

- **`apps/api`**: Main FastAPI application.
- **`packages/core`**: Core business logic.
- **`packages/ai`**: AI/Agent logic (Google Gemini).
- **`packages/parsers`**: Data parsers (BOM, etc).
- **`packages/database`**: Manages the PostgreSQL database connection.
- **`deployment/terraform`**: Terraform configuration for GCP infrastructure.


## Development

### Environment Files

| File | Purpose | Committed? |
|---|---|---|
| `.env.reference` | Example with all available variables | ✅ Yes |
| `.env` | Your local dev secrets | ❌ No |
| `.env.prod` | Production secrets (used by `deploy.sh`) | ❌ No |

Edit `.env` with your settings:

```bash
# Required for the /agent/ask endpoint
GEMINI_API_KEY=your-gemini-api-key

# PostgreSQL database connection string
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/interlock
```

### Prerequisites

| Tool | Purpose |
|---|---|
| [Python 3.12+](https://www.python.org/) | Runtime |
| [uv](https://docs.astral.sh/uv/) | Package manager (handles venv, deps, and running scripts) |
| [Docker](https://docs.docker.com/get-docker/) | Required for running the local PostgreSQL database |

Run the following to install python dependencies:

```bash
uv sync
```

### Database

Start the local PostgreSQL database using Docker Compose:

```bash
docker-compose up -d
```

This will spin up a Postgres container listening on port 5432. The data is persisted in a docker volume `postgres_data`.

#### Migrations

Migrations are handled with alembic. Run the following to upgrade the database to the latest schema:

```bash
cd packages/database
uv run alembic upgrade HEAD
```

### Linting

Run the linting script to check for issues:

```bash
./lint.sh
```

### Start the API

Run this from the root of the monorepo to start the local API:

```bash
uv run --package api uvicorn api.main:app --reload --env-file .env
```

### Frontend

See [Frontend_README](frontend/README.md) for instructions on running the frontend locally.

## Deployment 

Set up google cloud with authentication:

```bash
gcloud auth application-default login
```

Then run this script to deploy the stack using terraform to GCP:
```bash
./deploy.sh --env-file .env.prod
```

