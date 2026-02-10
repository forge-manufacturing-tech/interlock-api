#!/bin/bash

cd "$(dirname "$0")"

ENV_FILE=${1:-../../.env}

echo "Using environment file: $ENV_FILE"

uv run uvicorn main:app --reload --env-file "$ENV_FILE"