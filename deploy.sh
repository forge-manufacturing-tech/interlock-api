#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# deploy.sh — Idempotent deployment of the Interlock API to Google Cloud
#
# This script:
#   1. Builds a Docker image from the monorepo
#   2. Pushes it to Artifact Registry
#   3. Runs Terraform to converge all GCP infrastructure
#
# Usage:
#   ./deploy.sh                        # Deploy with defaults
#   ./deploy.sh --env-file .env.prod   # Deploy with production secrets
#   ./deploy.sh --plan                 # Preview changes without applying
#   ./deploy.sh --destroy              # Tear down all infrastructure
#
# Prerequisites:
#   - gcloud CLI (authenticated)
#   - docker
#   - terraform (>= 1.5)
#   - uv (for generating requirements.txt)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Resolve paths ────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/deployment/terraform"
BUILD_DIR="${SCRIPT_DIR}/build_deploy"

# ── Defaults ─────────────────────────────────────────────────────────────────

ENV_FILE=""
TF_ACTION="apply"
EXTRA_TF_ARGS=()

# ── Parse arguments ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --plan)
            TF_ACTION="plan"
            shift
            ;;
        --destroy)
            TF_ACTION="destroy"
            shift
            ;;
        --auto-approve)
            EXTRA_TF_ARGS+=("-auto-approve")
            shift
            ;;
        *)
            # Pass unknown args through to terraform
            EXTRA_TF_ARGS+=("$1")
            shift
            ;;
    esac
done

# ── Validate prerequisites ──────────────────────────────────────────────────

for cmd in gcloud docker terraform uv; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: '$cmd' is required but not installed." >&2
        exit 1
    fi
done

# ── Load tfvars ──────────────────────────────────────────────────────────────

if [[ ! -f "${TERRAFORM_DIR}/terraform.tfvars" ]]; then
    echo "ERROR: ${TERRAFORM_DIR}/terraform.tfvars not found."
    echo "Copy terraform.tfvars.example to terraform.tfvars and configure it."
    exit 1
fi

# Read project_id and region from tfvars (simple grep, no external deps)
PROJECT_ID=$(grep -E '^project_id\s*=' "${TERRAFORM_DIR}/terraform.tfvars" | sed 's/.*=\s*"\(.*\)"/\1/')
REGION=$(grep -E '^region\s*=' "${TERRAFORM_DIR}/terraform.tfvars" | sed 's/.*=\s*"\(.*\)"/\1/')
SERVICE_NAME=$(grep -E '^service_name\s*=' "${TERRAFORM_DIR}/terraform.tfvars" | sed 's/.*=\s*"\(.*\)"/\1/')

if [[ -z "$PROJECT_ID" || -z "$REGION" || -z "$SERVICE_NAME" ]]; then
    echo "ERROR: Could not read project_id, region, or service_name from terraform.tfvars"
    exit 1
fi

REPO_NAME="${SERVICE_NAME}-repo"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"

echo "═══════════════════════════════════════════════════════════════════════"
echo "  Interlock API — GCP Deployment"
echo "═══════════════════════════════════════════════════════════════════════"
echo "  Project:  ${PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  Service:  ${SERVICE_NAME}"
echo "  Image:    ${IMAGE_TAG}"
echo "  Action:   ${TF_ACTION}"
echo "═══════════════════════════════════════════════════════════════════════"

# ── If destroying, skip build and go straight to terraform ───────────────────

if [[ "$TF_ACTION" == "destroy" ]]; then
    echo ""
    echo "▸ Running terraform destroy..."
    cd "${TERRAFORM_DIR}"
    terraform init -input=false
    terraform destroy -var="docker_image=${IMAGE_TAG}" "${EXTRA_TF_ARGS[@]}"
    echo "✓ Infrastructure destroyed."
    exit 0
fi

# ── Step 1: Build Docker image ───────────────────────────────────────────────

echo ""
echo "▸ Step 1/5: Preparing build context..."

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# Copy API application code
echo "  Copying apps/api..."
cp -r "${SCRIPT_DIR}/apps/api/src/api" "${BUILD_DIR}/api"

# Copy internal packages (flattened for the container)
echo "  Copying internal packages..."
for pkg in core parsers ai database models orm auth; do
    src_layout="${SCRIPT_DIR}/packages/${pkg}/src/${pkg}"
    flat_layout="${SCRIPT_DIR}/packages/${pkg}/${pkg}"
    if [[ -d "$src_layout" ]]; then
        cp -r "$src_layout" "${BUILD_DIR}/${pkg}"
        echo "    ✓ ${pkg}"
    elif [[ -d "$flat_layout" ]]; then
        cp -r "$flat_layout" "${BUILD_DIR}/${pkg}"
        echo "    ✓ ${pkg}"
    else
        echo "    ⚠ ${pkg} not found, skipping"
    fi
done

# ── Step 2: Generate requirements.txt ────────────────────────────────────────

echo ""
echo "▸ Step 2/5: Generating requirements.txt..."

REQ_PATH="${BUILD_DIR}/requirements.txt"
uv export --package api --no-dev --format requirements-txt --no-hashes --output-file "$REQ_PATH"

# Filter out local workspace packages and add uvicorn
TMP_REQ=$(mktemp)
grep -v -E '(file://|^-e )' "$REQ_PATH" | grep -v '^\s*$' > "$TMP_REQ" || true
echo "uvicorn>=0.20.0" >> "$TMP_REQ"
mv "$TMP_REQ" "$REQ_PATH"

echo "  ✓ requirements.txt generated"

# ── Step 3: Generate Dockerfile ──────────────────────────────────────────────

echo ""
echo "▸ Step 3/5: Generating Dockerfile..."

cat > "${BUILD_DIR}/Dockerfile" <<'DOCKERFILE'
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
DOCKERFILE

echo "  ✓ Dockerfile generated"

# ── Step 4: Build & Push Docker image ────────────────────────────────────────

echo ""
echo "▸ Step 4/5: Building and pushing Docker image..."

# Ensure Artifact Registry docker auth is configured
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet 2>/dev/null || true

# Ensure the Artifact Registry repo exists (Terraform will also manage this,
# but we need it before the first `terraform apply` since the image must exist).
gcloud artifacts repositories describe "$REPO_NAME" \
    --project="$PROJECT_ID" \
    --location="$REGION" \
    --format="value(name)" 2>/dev/null || \
gcloud artifacts repositories create "$REPO_NAME" \
    --project="$PROJECT_ID" \
    --location="$REGION" \
    --repository-format=docker \
    --description="Docker images for ${SERVICE_NAME}" \
    --quiet

docker build -t "$IMAGE_TAG" "${BUILD_DIR}"
docker push "$IMAGE_TAG"

echo "  ✓ Image pushed: ${IMAGE_TAG}"

# ── Step 5: Terraform ────────────────────────────────────────────────────────

echo ""
echo "▸ Step 5/5: Running Terraform ${TF_ACTION}..."

# Load env vars from .env file into a Terraform variable
TF_ENV_VAR_ARG=""
if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
    echo "  Loading env vars from ${ENV_FILE}..."
    # Build a Terraform map from the .env file
    ENV_MAP="{"
    FIRST=true
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        # Skip comments and empty lines
        [[ -z "$key" || "$key" =~ ^# ]] && continue
        # Remove surrounding quotes from value
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        if [[ "$FIRST" == true ]]; then
            FIRST=false
        else
            ENV_MAP+=","
        fi
        ENV_MAP+="\"${key}\"=\"${value}\""
    done < "$ENV_FILE"
    ENV_MAP+="}"
    TF_ENV_VAR_ARG="-var=env_vars=${ENV_MAP}"
fi

cd "${TERRAFORM_DIR}"
terraform init -input=false

if [[ "$TF_ACTION" == "plan" ]]; then
    terraform plan \
        -var="docker_image=${IMAGE_TAG}" \
        ${TF_ENV_VAR_ARG:+"$TF_ENV_VAR_ARG"} \
        "${EXTRA_TF_ARGS[@]+"${EXTRA_TF_ARGS[@]}"}"
else
    terraform apply \
        -var="docker_image=${IMAGE_TAG}" \
        ${TF_ENV_VAR_ARG:+"$TF_ENV_VAR_ARG"} \
        "${EXTRA_TF_ARGS[@]+"${EXTRA_TF_ARGS[@]}"}"
fi

# ── Cleanup ──────────────────────────────────────────────────────────────────

rm -rf "${BUILD_DIR}"

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "  ✓ Deployment complete!"
if [[ "$TF_ACTION" != "plan" ]]; then
    SERVICE_URL=$(cd "${TERRAFORM_DIR}" && terraform output -raw service_url 2>/dev/null || echo "N/A")
    echo "  Service URL: ${SERVICE_URL}"
fi
echo "═══════════════════════════════════════════════════════════════════════"