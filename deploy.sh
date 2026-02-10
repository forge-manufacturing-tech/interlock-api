#!/bin/bash
set -e

uv run --package deploy-gcp deploy-gcp \
  --project-id interlock-485105 \
  --bucket interlock-api-source \
  --region us-central1 \
  --env-file .env.prod