# Interlock UI

This package contains the frontend UI for Interlock, built using [Rio](https://rio.dev).

## Setup

Ensure you have the API running locally or set the `API_URL` environment variable.

## Usage

To run the UI:

```bash
uv run --package ui -- python -m ui
```

Or while inside the `packages/ui` directory:

```bash
uv run python -m ui
```

## Configuration

The UI connects to the API URL defined by the `API_URL` environment variable, or defaults to `http://localhost:8000`.

To test against production:

```bash
API_URL=https://interlock-api-qwerty12345.a.run.app uv run python -m ui
```
