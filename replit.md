# Interlock API - Manufacturing Graph Intelligence

## Overview
A Python monorepo for managing manufacturing graphs, parts, and bill of materials (BOM). The system provides an AI-powered agent for querying and modifying the manufacturing graph, along with a modern React frontend for visualization and data management. Includes user authentication with JWT tokens and API key management for programmatic access.

## Architecture
- **Backend**: FastAPI API server (`apps/api`) running on port 8000
- **Frontend**: React + Vite + TypeScript app (`frontend/`) running on port 5000, proxies API requests to backend
- **Database**: SQLite (file-based, configured via `DB_PATH` env var, default `./data/interlock.db`)
- **AI Agent**: LangChain-based agent using OpenAI via Replit AI Integrations (`packages/ai`), supports multimodal inputs (PDF, images)
- **Auth**: JWT-based authentication with API key support (`packages/auth`)

## Project Structure
```
├── apps/
│   └── api/             # FastAPI backend API
│       └── src/api/     # API source (main.py, logging_config.py)
├── frontend/            # React + Vite + TypeScript frontend
│   ├── src/
│   │   ├── api/         # Auto-generated TypeScript API client (from OpenAPI)
│   │   ├── components/  # Reusable components (Navbar, DashboardLayout)
│   │   ├── lib/         # Auth context provider
│   │   └── pages/       # Page components (Landing, Login, Dashboard pages)
│   ├── openapi.json     # OpenAPI spec (source for code generation)
│   └── vite.config.ts   # Vite config with API proxy
├── packages/
│   ├── ai/              # AI agent logic (LangChain + OpenAI via Replit AI)
│   ├── auth/            # Authentication (JWT, API keys, user management)
│   ├── core/            # Core shared utilities
│   ├── database/        # SQLite database manager
│   ├── models/          # Pydantic data models
│   ├── orm/             # CRUD repository for manufacturing graph
│   └── parsers/         # BOM file parsers (Excel, DXF, etc.)
├── pyproject.toml       # Root workspace config (uv workspaces)
└── uv.lock              # Dependency lock file
```

## Tech Stack
- **Language**: Python 3.12 (backend), TypeScript (frontend)
- **Package Manager**: uv (workspace mode, backend), npm (frontend)
- **Backend Framework**: FastAPI + Uvicorn
- **Frontend Framework**: React + Vite + Tailwind CSS v4
- **API Client**: Auto-generated from OpenAPI spec using openapi-typescript-codegen
- **State Management**: React Query (@tanstack/react-query), React Context (auth)
- **Routing**: React Router v6
- **Database**: SQLite
- **AI**: LangChain, LangGraph, OpenAI via Replit AI Integrations
- **Auth**: bcrypt (password hashing), PyJWT (tokens)

## Environment Variables
- `DB_PATH`: Path to SQLite database file (default: `./data/interlock.db`)
- `AI_INTEGRATIONS_OPENAI_API_KEY`: Auto-set by Replit AI Integrations (do not modify)
- `AI_INTEGRATIONS_OPENAI_BASE_URL`: Auto-set by Replit AI Integrations (do not modify)
- `JWT_SECRET`: Secret key for JWT token signing (required)
- `JWT_EXP_MINUTES`: JWT token expiry in minutes (default: 1440 = 24 hours)

## Authentication
- **Web UI**: Users sign up/login via the React frontend; JWT stored in localStorage
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

## Frontend API Client Generation
The TypeScript API client is auto-generated from the backend's OpenAPI spec:
```bash
cd frontend
curl -s http://127.0.0.1:8000/openapi.json > openapi.json
npx openapi-typescript-codegen --input openapi.json --output src/api --client fetch
```

## Running the Application
The workflow runs both backend and frontend:
- Backend: `uv run uvicorn api.main:app --host 127.0.0.1 --port 8000`
- Frontend: `cd frontend && npm run dev` (Vite dev server on port 5000, proxies `/api` to backend)

## Design System
- **Theme**: Dark mode with orange (#EC5B13) primary accent
- **Fonts**: JetBrains Mono (headings/monospace), Inter (body)
- **Background**: #09090B (surface), #18181B (panels), #27272A (borders)
- **Inspired by**: https://interlock-systems.netlify.app

## Recent Changes
- 2026-02-14: Added multimodal chat - agent accepts PDF uploads (text extraction via PyMuPDF) and images (analyzed via OpenAI vision), tree export as CSV BOM and markdown work instructions
- 2026-02-14: Switched AI agent from Google Gemini to Replit AI Integrations (OpenAI-compatible, gpt-5/gpt-5-mini)
- 2026-02-14: Replaced Streamlit frontend with React + Vite + TypeScript app, auto-generated API client from OpenAPI, added landing page, dashboard with parts/trees/BOM/agent/API keys pages
- 2026-02-14: Added authentication system - user signup/login with JWT, API key management, protected API routes
- 2026-02-14: Initial Replit setup - restructured apps/api to src layout, installed graphviz system dependency
