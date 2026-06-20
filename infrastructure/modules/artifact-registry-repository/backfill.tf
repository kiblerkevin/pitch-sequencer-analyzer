variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "environment" {
  type = string
}

variable "immutable_tags" {
  description = "Whether to enforce immutable tags (use true for staging/prod)"
  type        = bool
  default     = false
}

resource "google_artifact_registry_repository" "backfill" {
  project       = var.project_id
  location      = var.region
  repository_id = "psa-${var.environment}-backfill"
  format        = "DOCKER"

  docker_config {
    immutable_tags = var.immutable_tags
  }
}

output "repository_id" {
  description = "Artifact Registry Repository ID"
  value = google_artifact_registry_repository.backfill.repository_id
}

output "repository_url" {
  description = "Artifact Registry Repository URL"
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backfill.repository_id}"
}
