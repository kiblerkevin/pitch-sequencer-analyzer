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

resource "google_cloud_run_v2_job" "daily_ingestion" {
  name     = "psa-${var.environment}-daily-ingestion-job"
  location = var.region
  project  = var.project_id

  template {
    template {
      containers {
        image = "${var.repository_url}/backfill:latest"
        args  = ["--bucket", var.bucket_name, "--daily"]
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

resource "google_service_account" "scheduler" {
  project      = var.project_id
  account_id   = "psa-${var.environment}-scheduler"
  display_name = "PSA Cloud Scheduler (${var.environment})"
}

resource "google_project_iam_member" "scheduler_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "daily_ingestion" {
  name             = "psa-${var.environment}-daily-ingestion"
  project          = var.project_id
  region           = var.region
  description      = "Triggers daily MLB Statcast ingestion at 6am CT"
  schedule         = "0 11 * * *"
  time_zone        = "America/Chicago"
  attempt_deadline = "1800s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/psa-${var.environment}-daily-ingestion-job:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}
