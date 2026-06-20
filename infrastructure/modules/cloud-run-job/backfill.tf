variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "environment" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "repository_url" {
  description = "Full Artifact Registry repository URL (e.g., us-central1-docker.pkg.dev/project/repo)"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for the job to run as"
  type        = string
}

resource "google_cloud_run_v2_job" "backfill" {
  name     = "psa-${var.environment}-backfill-job"
  location = var.region
  project  = var.project_id

  template {
    template {
      containers {
        image = "${var.repository_url}/backfill:latest"
        args  = ["--bucket", var.bucket_name]
        resources {
          limits = {
            memory = "2048Mi"
          }
        }
      }
      timeout         = "1800s"
      service_account = var.service_account_email
    }
  }
}
