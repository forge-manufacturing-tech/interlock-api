# Interlock API - Manufacturing Graph Intelligence

## Overview
A Python monorepo for managing manufacturing graphs, parts, and bill of materials (BOM). The system provides an AI-powered agent for querying and modifying the manufacturing graph, along with a web-based frontend for visualization and data management. Includes user authentication with JWT tokens and API key management for programmatic access.

## Architecture
- **Backend**: FastAPI API server (`apps/api`) running on port 8000
- **Frontend**: Streamlit app (`packages/frontend`) running on port 5000
- **Database**: SQLite (file-based, configured via `DB_PATH` env var, default `./data/interlock.db`)
- **AI Agent**: LangChain-based agent using Google Gemini (`packages/ai`)
- **Auth**: JWT-based authentication with API key support (`packages/auth`)

## Project Structure
```
├── apps/
│   └── api/             # FastAPI backend API
│       └── src/api/     # API source (main.py, logging_config.py)
├── packages/
│   ├── ai/              # AI agent logic (LangChain + Gemini)
│   ├── auth/            # Authentication (JWT, API keys, user management)
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
- **Auth**: bcrypt (password hashing), PyJWT (tokens)

## Environment Variables
- `DB_PATH`: Path to SQLite database file (default: `./data/interlock.db`)
- `GEMINI_API_KEY`: Google Gemini API key (required for AI agent features)
- `JWT_SECRET`: Secret key for JWT token signing (required)
- `JWT_EXP_MINUTES`: JWT token expiry in minutes (default: 1440 = 24 hours)

## Authentication
- **Web UI**: Users sign up/login via the Streamlit frontend; JWT stored in session state
- **API Access**: Two methods supported:
  - Bearer token: `Authorization: Bearer <jwt_token>`
  - API key: `x-api-key: <api_key>` header
- **Auth Endpoints** (unprotected):
  - `POST /auth/signup` - Create account
  - `POST /auth/login` - Sign in
- **Auth Endpoints** (protected):
  - `GET /auth/me` - Get current user
  - `POST /auth/api-keys` - Create API key
  - `GET /auth/api-keys` - List API keys
  - `DELETE /auth/api-keys/{key_id}` - Revoke API key
- All other API endpoints require authentication

## Running the Application
The workflow runs both backend and frontend:
- Backend: `uv run uvicorn api.main:app --host 127.0.0.1 --port 8000`
- Frontend: `uv run streamlit run packages/frontend/src/frontend/main.py` (port 5000)

## Recent Changes
- 2026-02-14: Added authentication system - user signup/login with JWT, API key management, protected API routes, Streamlit auth UI
- 2026-02-14: Initial Replit setup - restructured apps/api to src layout, configured Streamlit for Replit proxy, installed graphviz system dependency
