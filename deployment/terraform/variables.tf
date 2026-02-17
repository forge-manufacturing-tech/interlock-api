# ──────────────────────────────────────────────────────────────────────────────
# Interlock API – GCP Deployment Variables
# ──────────────────────────────────────────────────────────────────────────────

variable "project_id" {
  description = "The GCP project ID to deploy into."
  type        = string
}

variable "region" {
  description = "The GCP region for all resources."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The Cloud Run service name."
  type        = string
  default     = "interlock-api"
}

variable "docker_image" {
  description = "Full path to the Docker image (built and pushed by deploy.sh)."
  type        = string
}

# ── Environment Variables ────────────────────────────────────────────────────

variable "env_vars" {
  description = "Map of environment variables to set on the Cloud Run service."
  type        = map(string)
  default     = {}
  sensitive   = true
}

# ── Cloud Run Configuration ──────────────────────────────────────────────────

variable "memory" {
  description = "Memory limit for the Cloud Run service (e.g. '1Gi', '2Gi')."
  type        = string
  default     = "1Gi"
}

variable "cpu" {
  description = "CPU limit for the Cloud Run service (e.g. '1', '2')."
  type        = string
  default     = "1"
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances."
  type        = number
  default     = 10
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances (0 = scale to zero)."
  type        = number
  default     = 0
}

variable "container_port" {
  description = "Port the container listens on."
  type        = number
  default     = 8080
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated (public) access to the Cloud Run service."
  type        = bool
  default     = false
}
