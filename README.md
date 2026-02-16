# Interlock API

This is the API for the Interlock monorepo. It is a FastAPI application that provides a REST API for the Interlock system.

## Project Structure

- **`apps/api`**: Main FastAPI application.
- **`packages/core`**: Core business logic.
- **`packages/ai`**: AI/Agent logic (Google Gemini).
- **`packages/parsers`**: Data parsers (BOM, etc).
- **`packages/database`**: Manages the PostgreSQL database connection.
- **`deployment/terraform`**: Terraform configuration for GCP infrastructure.

## Local Development Setup

### Prerequisites

| Tool | Purpose |
|---|---|
| [Python 3.12+](https://www.python.org/) | Runtime |
| [uv](https://docs.astral.sh/uv/) | Package manager (handles venv, deps, and running scripts) |
| [Docker](https://docs.docker.com/get-docker/) | Required for running the local PostgreSQL database |

### 1. Install dependencies

```bash
uv venv
uv sync
```

### 2. Configure environment variables

Copy the reference file and fill in your values:

```bash
cp .env.reference .env
```

Edit `.env` with your settings:

```bash
# Required for the /agent/ask endpoint
GEMINI_API_KEY=your-gemini-api-key

# PostgreSQL database connection string
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/interlock
```

### 3. Start the Database

Start the local PostgreSQL database using Docker Compose:

```bash
docker-compose up -d
```

This will spin up a Postgres container listening on port 5432. The data is persisted in a docker volume `postgres_data`.

### 4. Start the API

```bash
uv run --package api uvicorn api.main:app --reload --env-file .env
```

The API will be available at **http://127.0.0.1:8000**:

| Endpoint | Description |
|---|---|
| `GET /` | System status |
| `GET /docs` | OpenAPI (Swagger) docs |
| `GET /api-docs` | Scalar API reference |
| `POST /ingest/bom` | Upload and parse a BOM file |
| `POST /agent/ask` | Ask the AI agent a question |

### Environment Files

| File | Purpose | Committed? |
|---|---|---|
| `.env.reference` | Example with all available variables | ✅ Yes |
| `.env` | Your local dev secrets | ❌ No |
| `.env.prod` | Production secrets (used by `deploy.sh`) | ❌ No |

To start the API with production variables (for testing locally):

```bash
./apps/api/start.sh ./.env.prod
```

## Development

### Linting

Run the linting script to check for issues:

```bash
./lint.sh
```

This runs both `ruff` (linter/formatter) and `ty` (type checker).

To fix formatting issues automatically:

```bash
uv run ruff format .
uv run ruff check --fix .
```

### VS Code / Cursor Setup

This project handles Python tooling via `uv`. For the best experience in VS Code or Cursor:

1.  **Install Recommended Extensions**:
    *   **Ruff** (`charliermarsh.ruff`): For linting and formatting.
    *   **Ty** (`astral-sh.ty`): For fast type checking.

2.  **Configuration**:
    The project includes pre-configured settings in `.vscode/settings.json` that enable:
    *   Formatting on save with Ruff.
    *   Organizing imports on save.
    *   Fixing lint issues on save.

    Simply open the project in VS Code / Cursor and accept the recommended extensions.


## Deployment (Static Site)

The frontend is deployed automatically to GitHub Pages via a GitHub Action.

### Prerequisites

1.  Go to your repository **Settings** > **Pages**.
2.  Under **Build and deployment** > **Source**, select **GitHub Actions**.
3.  The workflow `.github/workflows/deploy-static.yml` will automatically build and deploy the `frontend/` directory on every push to `main`.

### Workflow Details

The [Deploy Static Content to Pages](.github/workflows/deploy-static.yml) workflow:
1.  Triggers on push to `main` (only if `frontend/**` changes) or manual dispatch.
2.  Builds the frontend using `npm run build`.
3.  Uploads the `dist` folder as a GitHub Pages artifact.
4.  Deploys the artifact to GitHub Pages.

### Manual Trigger

You can also manually trigger the deployment from the **Actions** tab in GitHub by selecting the "Deploy Static Content to Pages" workflow and clicking **Run workflow**.

## Running with Docker (Full Stack - Local)

You can run the entire stack (Database, API, Frontend) using Docker Compose for local development:

```bash
# Build and start all services
docker-compose up --build
```

This will spin up:
- **Frontend**: http://localhost:5000
- **API**: http://localhost:8000
- **Database**: postgres:5432 (internal to docker network)

