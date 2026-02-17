# Interlock Frontend

This is the React frontend for the Interlock platform, built with [Vite](https://vitejs.dev/) and [Bun](https://bun.sh/).

## Prerequisites

- [Bun](https://bun.sh/) (latest version)
- Active backend API running on `http://127.0.0.1:8000`

## Setup

1. **Install dependencies**:
   ```bash
   bun install
   ```

## API URL

Set the API url by setting the environment variable:

```bash
export VITE_API_URL="http://127.0.0.1:8000"
```

## Development

To start the development server:

```bash
bun run dev
```

The application will be available at **http://localhost:5000**.

### API Connection

The frontend is configured to proxy requests to the backend API.
- **Frontend URL**: `http://localhost:5000`
- **Backend URL**: `http://127.0.0.1:8000`
- **Proxy Rule**: Requests starting with `/api` are forwarded to the backend.

See `vite.config.ts` for proxy configuration details.

## Building for Production

To build the application for production:

```bash
bun run build
```

The build artifacts will be output to the `dist` directory.

## Docker

To build and run the frontend as a Docker container:

```bash
# Build the image
docker build -t interlock-frontend .

# Run the container (mapping port 5000 to 80)
# Ensure API is accessible at /api endpoint or configure VITE_API_URL
docker run -p 5000:80 interlock-frontend
```

## Linting

To run the linter:


## API Client Generation

To regenerate the API client from `openapi.json`:

```bash
bun run generate-client
```

To regenerate from a running backend (e.g. if `VITE_API_URL` is set to your backend):

```bash
# Replace with your actual backend URL
bunx openapi-typescript-codegen --input http://localhost:8000/openapi.json --output src/api --client fetch
```

The client is automatically configured to use `VITE_API_URL` at runtime in `src/main.tsx`.

