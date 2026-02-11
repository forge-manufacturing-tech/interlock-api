# Interlock API

This is the API for the Interlock monorepo. It is a FastAPI application that provides a REST API for the Interlock system.

## Project Structure

- **`apps/api`**: Main FastAPI application.
- **`packages/core`**: Core business logic.
- **`packages/ai`**: AI/Agent logic (Google Gemini).
- **`packages/parsers`**: Data parsers (BOM, etc).
- **`packages/database`**: Manages the Kùzu graph database connection, supporting local files and cloud-mounted storage.
- **`deployment/terraform`**: Terraform configuration for GCP infrastructure.

## Local Development Setup

### Prerequisites

| Tool | Purpose |
|---|---|
| [Python 3.12+](https://www.python.org/) | Runtime |
| [uv](https://docs.astral.sh/uv/) | Package manager (handles venv, deps, and running scripts) |

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

# Kùzu database stored as local files (created automatically)
KUZU_DB_PATH=./data/interlock.kuzu

# Optional: path to a separate read-only public graph
# KUZU_PUBLIC_DB_PATH=./data/interlock_public.kuzu
```

> **How the database works locally:** Kùzu is an embedded graph database — no server needed. When you set `KUZU_DB_PATH=./data/interlock.kuzu`, a folder called `data/interlock.kuzu/` is created in the project root containing the database files. This folder is gitignored and persists between restarts.

### 3. Start the API

```bash
./apps/api/start.sh
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


## Deployment

Deployment is **idempotent** and managed by [Terraform](https://www.terraform.io/). Running `./deploy.sh` multiple times is always safe — it will only create or update resources that differ from the desired state.

### Prerequisites

| Tool | Purpose |
|---|---|
| [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | `gcloud` CLI, authentication |
| [Terraform](https://developer.hashicorp.com/terraform/install) (>= 1.5) | Infrastructure-as-code |
| [Docker](https://docs.docker.com/get-docker/) | Container builds |
| uv | Already set up in this repo |

Authenticate with GCP:
```bash
gcloud auth login
gcloud auth application-default login
```

### Configure

```bash
# Copy the example and fill in your values
cp deployment/terraform/terraform.tfvars.example \
   deployment/terraform/terraform.tfvars
```

### Deploy

```bash
# Preview changes (dry-run)
./deploy.sh --plan

# Deploy with production secrets
./deploy.sh --env-file .env.prod

# Non-interactive deployment (CI/CD)
./deploy.sh --env-file .env.prod --auto-approve

# Tear down everything
./deploy.sh --destroy
```

### What Gets Deployed

All infrastructure is managed by Terraform — no manual `gcloud` commands needed:

- **Cloud Run** service with auto-scaling
- **Artifact Registry** Docker repository
- **GCS Buckets** for Kùzu graph databases (private + public), mounted via GCS FUSE
- **IAM** bindings for the service account and (optionally) public access
- **Required GCP APIs** enabled automatically

### Database: Local vs Cloud

| | Local Development | Cloud (GCP) |
|---|---|---|
| **Storage** | Local filesystem (`./data/interlock.kuzu/`) | GCS bucket mounted as a volume via GCS FUSE |
| **Config** | `KUZU_DB_PATH` in `.env` | Auto-set by Terraform to `/data/graph/interlock.kuzu` |
| **Public DB** | Optional local path | Separate GCS bucket at `/data/public_graph/interlock_public.kuzu` |
| **Persistence** | Survives restarts, lives in project dir | Versioned GCS bucket, survives container restarts |