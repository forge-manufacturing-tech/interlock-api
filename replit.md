# Interlock API - Manufacturing Graph Intelligence

## Overview
A Python monorepo for managing manufacturing graphs, parts, and bill of materials (BOM). The system provides an AI-powered agent for querying and modifying the manufacturing graph, along with a web-based frontend for visualization and data management.

## Architecture
- **Backend**: FastAPI API server (`apps/api`) running on port 8000
- **Frontend**: Streamlit app (`packages/frontend`) running on port 5000
- **Database**: SQLite (file-based, configured via `DB_PATH` env var, default `./data/interlock.db`)
- **AI Agent**: LangChain-based agent using Google Gemini (`packages/ai`)

## Project Structure
```
├── apps/
│   └── api/             # FastAPI backend API
│       └── src/api/     # API source (main.py, logging_config.py)
├── packages/
│   ├── ai/              # AI agent logic (LangChain + Gemini)
│   ├── core/            # Core shared utilities
│   ├── database/        # SQLite database manager
│   ├── frontend/        # Streamlit web frontend
│   ├── models/          # Pydantic data models
│   ├── orm/             # CRUD repository for manufacturing graph
│   └── parsers/         # BOM file parsers (Excel, DXF, etc.)
├── pyproject.toml       # Root workspace config (uv workspaces)
└── uv.lock              # Dependency lock file
```

## Tech Stack
- **Language**: Python 3.12
- **Package Manager**: uv (workspace mode)
- **Backend Framework**: FastAPI + Uvicorn
- **Frontend Framework**: Streamlit
- **Database**: SQLite
- **AI**: LangChain, LangGraph, Google Gemini

## Environment Variables
- `DB_PATH`: Path to SQLite database file (default: `./data/interlock.db`)
- `GEMINI_API_KEY`: Google Gemini API key (required for AI agent features)

## Running the Application
The workflow runs both backend and frontend:
- Backend: `uv run uvicorn api.main:app --host 127.0.0.1 --port 8000`
- Frontend: `uv run streamlit run packages/frontend/src/frontend/main.py` (port 5000)

## Recent Changes
- 2026-02-14: Initial Replit setup - restructured apps/api to src layout, configured Streamlit for Replit proxy, installed graphviz system dependency
