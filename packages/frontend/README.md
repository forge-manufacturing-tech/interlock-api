# Interlock Frontend

This is a Streamlit application for interacting with the Interlock Manufacturing API.

## Setup

Ensure you have the API running at `http://127.0.0.1:8000`.

## Installation

This package uses `uv`. To run the application:

```bash
# From the root of the workspace
uv run --package frontend streamlit run packages/frontend/src/frontend/main.py
```

Or if you are inside `packages/frontend`:

```bash
uv run streamlit run src/frontend/main.py
```

## Features

- **Agent Chat**: Chat with the manufacturing AI agent.
- **Parts Explorer**: View and filter parts in the manufacturing graph.
- **BOM Ingestion**: Upload Bill of Materials (CSV, Excel, JSON).
