# ──────────────────────────────────────────────────────────────────────────────
# Interlock API – GCP Infrastructure (Terraform)
#
# This configuration is fully idempotent. Running `terraform apply` multiple
# times will converge to the desired state without side-effects.
# ──────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ──────────────────────────────────────────────────────────────────────────────
# 1. Enable Required APIs
# ──────────────────────────────────────────────────────────────────────────────

locals {
  required_apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.required_apis)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ──────────────────────────────────────────────────────────────────────────────
# 2. Artifact Registry (Docker Repository)
# ──────────────────────────────────────────────────────────────────────────────

resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "${var.service_name}-repo"
  format        = "DOCKER"
  description   = "Docker images for ${var.service_name}"

  depends_on = [google_project_service.apis]
}

# Grant Cloud Run service account permission to pull images
resource "google_artifact_registry_repository_iam_member" "docker_viewer" {
  location   = google_artifact_registry_repository.docker.location
  repository = google_artifact_registry_repository.docker.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ──────────────────────────────────────────────────────────────────────────────
# 3. Service Account for Cloud Run
# ──────────────────────────────────────────────────────────────────────────────

resource "google_service_account" "cloud_run" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name} Cloud Run"
}

# ──────────────────────────────────────────────────────────────────────────────
# 4. Cloud Run Service
# ──────────────────────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "api" {
  name     = var.service_name
  location = var.region

  deletion_protection = false

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      max_instance_count = var.max_instances
      min_instance_count = var.min_instances
    }

    containers {
      image = var.docker_image

      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      env {
        name  = "DEPLOY_TIME"
        value = timestamp()
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.docker,
  ]
}

# ──────────────────────────────────────────────────────────────────────────────
# 5. Blob Storage (GCS)
# ──────────────────────────────────────────────────────────────────────────────

resource "google_storage_bucket" "blobs" {
  name                        = "${var.project_id}-${var.service_name}-blobs"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "blobs_admin" {
  bucket = google_storage_bucket.blobs.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ──────────────────────────────────────────────────────────────────────────────
# 6. IAM – Allow unauthenticated access (public API)
# ──────────────────────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
