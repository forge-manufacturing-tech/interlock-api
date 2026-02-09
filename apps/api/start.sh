#!/bin/bash

cd "$(dirname "$0")"

uv run uvicorn main:app --reload