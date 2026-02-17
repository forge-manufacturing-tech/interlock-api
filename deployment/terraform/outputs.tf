# ──────────────────────────────────────────────────────────────────────────────
# Outputs
# ──────────────────────────────────────────────────────────────────────────────

output "service_url" {
  description = "The public URL of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.api.uri
}

output "service_account_email" {
  description = "The service account email used by Cloud Run."
  value       = google_service_account.cloud_run.email
}

output "artifact_registry_url" {
  description = "The Artifact Registry docker repository URL."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}
