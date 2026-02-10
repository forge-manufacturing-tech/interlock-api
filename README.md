# Interlock API

This is the API for the Interlock monorepo. It is a FastAPI application that provides a REST API for the Interlock system.

## Setup

```bash
uv venv
uv sync
```

Start the API:

```bash
./apps/api/start.sh
```

### Environment Variables

The API uses `.env` files for configuration.

See `.env.reference` for an example environment file.

1. Create a `.env` file in the root for **local development**:
    ```bash
    GEMINI_API_KEY=your_local_key
    ```
2. Create a `.env.prod` file in the root for **production secrets** (used by deploy script):
    ```bash
    GEMINI_API_KEY=your_production_key
    ```

**Note:** Do NOT commit these files to git.

To run locally with the **production** environment (to test before deploy):
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

The API can be deployed to Google Cloud Functions using the provided Python script.

### Prerequisites

1.  **GCP Project**: Ensure you have a Google Cloud Project with Cloud Functions, Cloud Build, and Cloud Storage APIs enabled.
2.  **Storage Bucket**: Create a GCS bucket to store the source code (e.g., `interlock-api-source`).
3.  **Authentication**: Ensure you are authenticated with `gcloud` or have `GOOGLE_APPLICATION_CREDENTIALS` set.

```bash
gcloud auth application-default login
```

### Deploying

### Deploying

Run the deployment script:

```bash
./deploy.sh
```

This script automatically reads secrets from the `.env.prod` file and deploys the API to Cloud Run. Make sure your `GEMINI_API_KEY` is set in `.env.prod` before deploying.