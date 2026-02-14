# Interlock API - Manufacturing Graph Intelligence

## Overview
A Python monorepo for managing manufacturing graphs, parts, and bill of materials (BOM). The system provides an AI-powered agent for querying and modifying the manufacturing graph, along with a modern React frontend for visualization and data management. Includes user authentication with JWT tokens and API key management for programmatic access.

## Architecture
- **Backend**: FastAPI API server (`apps/api`) running on port 8000 (dev) or port 5000 (production, serving static frontend)
- **Frontend**: React + Vite + TypeScript app (`frontend/`) running on port 5000 (dev), proxies API requests to backend
- **Database**: PostgreSQL (Replit built-in, Neon-backed, configured via `DATABASE_URL` env var)
- **AI Agent**: LangChain-based agent using OpenAI via Replit AI Integrations (`packages/ai`), supports multimodal inputs (PDF, images)
- **Auth**: JWT-based authentication with API key support (`packages/auth`)
- **Deployment**: Autoscale mode - backend serves both API and built frontend static files on single port 5000

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
│   ├── database/        # PostgreSQL database manager (psycopg2)
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
- **Database**: PostgreSQL (Replit built-in, via psycopg2)
- **AI**: LangChain, LangGraph, OpenAI via Replit AI Integrations
- **Auth**: bcrypt (password hashing), PyJWT (tokens)

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (auto-set by Replit)
- `AI_INTEGRATIONS_OPENAI_API_KEY`: Auto-set by Replit AI Integrations (do not modify)
- `AI_INTEGRATIONS_OPENAI_BASE_URL`: Auto-set by Replit AI Integrations (do not modify)
- `JWT_SECRET`: Secret key for JWT token signing (required)
- `JWT_EXP_MINUTES`: JWT token expiry in minutes (default: 1440 = 24 hours)

## Authentication & Authorization
- **Web UI**: Users sign up/login via the React frontend; JWT stored in localStorage
- **API Access**: Two methods supported:
  - Bearer token: `Authorization: Bearer <jwt_token>`
  - API key: `x-api-key: <api_key>` header
- **Roles**: `admin` (first user created) and `member` (all subsequent users)
- **AI Access**: Members cannot use the AI agent unless an admin enables `ai_enabled` for them. Admins always have AI access.
- **Auth Endpoints** (unprotected):
  - `POST /auth/signup` - Create account (first user becomes admin)
  - `POST /auth/login` - Sign in
- **Auth Endpoints** (protected):
  - `GET /auth/me` - Get current user (includes role, ai_enabled)
  - `POST /auth/api-keys` - Create API key
  - `GET /auth/api-keys` - List API keys
  - `DELETE /auth/api-keys/{key_id}` - Revoke API key
- **Admin Endpoints** (admin only):
  - `GET /auth/admin/users` - List all users
  - `PATCH /auth/admin/users/{user_id}` - Update user role/AI access
- All other API endpoints require authentication; agent chat requires AI access

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

## Deployment (Autoscale)
- Build: `cd frontend && npm run build` (outputs to `frontend/dist/`)
- Run: `uv run uvicorn api.main:app --host 0.0.0.0 --port 5000` (serves API + static frontend)
- Backend detects `frontend/dist/` and serves SPA with catch-all route for client-side routing

## Database Notes
- PostgreSQL with psycopg2 (RealDictCursor for dict rows)
- Schema initialization uses autocommit DDL (execute_ddl) to avoid lock contention
- Singleton database connections per module (auth, orm) to prevent concurrent schema init deadlocks
- Manual transaction management: autocommit=False for DML, explicit commit/rollback required

## Design System
- **Theme**: Dark mode with orange (#EC5B13) primary accent
- **Fonts**: JetBrains Mono (headings/monospace), Inter (body)
- **Background**: #09090B (surface), #18181B (panels), #27272A (borders)
- **Inspired by**: https://interlock-systems.netlify.app

## Recent Changes
- 2026-02-14: Migrated database from SQLite to PostgreSQL for autoscale deployment compatibility; converted all SQL syntax (placeholders, ON CONFLICT, BOOLEAN types, DOUBLE PRECISION, NOW()); added singleton DB connections and autocommit DDL to prevent lock deadlocks
- 2026-02-14: Configured autoscale deployment - backend serves frontend static files in production on single port 5000
- 2026-02-14: Added role-based access control - first user is admin, subsequent users are members; admins can enable/disable AI access per user via User Management page
- 2026-02-14: Added multimodal chat - agent accepts PDF uploads (text extraction via PyMuPDF) and images (analyzed via OpenAI vision), tree export as CSV BOM and markdown work instructions
- 2026-02-14: Switched AI agent from Google Gemini to Replit AI Integrations (OpenAI-compatible, gpt-5/gpt-5-mini)
- 2026-02-14: Replaced Streamlit frontend with React + Vite + TypeScript app, auto-generated API client from OpenAPI, added landing page, dashboard with parts/trees/BOM/agent/API keys pages
- 2026-02-14: Added authentication system - user signup/login with JWT, API key management, protected API routes
- 2026-02-14: Initial Replit setup - restructured apps/api to src layout, installed graphviz system dependency
