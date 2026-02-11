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

  # Optional: remote backend for team use.  Uncomment and configure as needed.
  # backend "gcs" {
  #   bucket = "your-tf-state-bucket"
  #   prefix = "interlock-api"
  # }
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
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
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

# ──────────────────────────────────────────────────────────────────────────────
# 3. GCS Buckets for Kùzu Graph Database (conditional)
# ──────────────────────────────────────────────────────────────────────────────

locals {
  # Derive globally-unique bucket names from project_id when not explicitly set
  private_graph_bucket_name = var.private_graph_bucket_name != "" ? var.private_graph_bucket_name : "${var.project_id}-private-graph"
  public_graph_bucket_name  = var.public_graph_bucket_name != "" ? var.public_graph_bucket_name : "${var.project_id}-public-graph"
}

resource "google_storage_bucket" "private_graph" {
  count = var.enable_private_graph ? 1 : 0

  name          = local.private_graph_bucket_name
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket" "public_graph" {
  count = var.enable_public_graph ? 1 : 0

  name          = local.public_graph_bucket_name
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  depends_on = [google_project_service.apis]
}

# ──────────────────────────────────────────────────────────────────────────────
# 4. Service Account for Cloud Run
# ──────────────────────────────────────────────────────────────────────────────

resource "google_service_account" "cloud_run" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name} Cloud Run"
}

# Grant the service account access to private graph bucket
resource "google_storage_bucket_iam_member" "private_graph_access" {
  count = var.enable_private_graph ? 1 : 0

  bucket = google_storage_bucket.private_graph[0].name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant the service account access to public graph bucket
resource "google_storage_bucket_iam_member" "public_graph_access" {
  count = var.enable_public_graph ? 1 : 0

  bucket = google_storage_bucket.public_graph[0].name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ──────────────────────────────────────────────────────────────────────────────
# 5. Cloud Run Service
# ──────────────────────────────────────────────────────────────────────────────

locals {
  # Base env vars from user config
  base_env_vars = var.env_vars

  # Graph-specific env vars (added conditionally)
  graph_env_vars = merge(
    var.enable_private_graph ? { KUZU_DB_PATH = "/data/graph/interlock.kuzu" } : {},
    var.enable_public_graph ? { KUZU_PUBLIC_DB_PATH = "/data/public_graph/interlock_public.kuzu" } : {},
  )

  all_env_vars = merge(local.base_env_vars, local.graph_env_vars)

  # Determine execution environment: gen2 required for GCS FUSE
  needs_fuse     = var.enable_private_graph || var.enable_public_graph
  execution_env  = local.needs_fuse ? "EXECUTION_ENVIRONMENT_GEN2" : null
}

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

    dynamic "volumes" {
      for_each = var.enable_private_graph ? [1] : []
      content {
        name = "private-graph"
        gcs {
          bucket    = google_storage_bucket.private_graph[0].name
          read_only = false
        }
      }
    }

    dynamic "volumes" {
      for_each = var.enable_public_graph ? [1] : []
      content {
        name = "public-graph"
        gcs {
          bucket    = google_storage_bucket.public_graph[0].name
          read_only = false
        }
      }
    }

    execution_environment = local.execution_env

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
        for_each = local.all_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "volume_mounts" {
        for_each = var.enable_private_graph ? [1] : []
        content {
          name       = "private-graph"
          mount_path = "/data/graph"
        }
      }

      dynamic "volume_mounts" {
        for_each = var.enable_public_graph ? [1] : []
        content {
          name       = "public-graph"
          mount_path = "/data/public_graph"
        }
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.docker,
  ]
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
