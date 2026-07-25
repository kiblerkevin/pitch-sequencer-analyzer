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

variable "image_tag" {
  description = "Image tag to deploy for the reference job"
  type        = string
  default     = "latest"
}

resource "google_cloud_run_v2_job" "reference" {
  name                = "psa-${var.environment}-reference-job"
  location            = var.region
  project             = var.project_id
  deletion_protection = false

  template {
    template {
      containers {
        image   = "${var.repository_url}/reference:${var.image_tag}"
        command = ["/usr/local/bin/python3", "-m", "app.reference"] {
  name             = "psa-${var.environment}-daily-reference"
  project          = var.project_id
  region           = var.region
  description      = "Triggers daily MLB reference data refresh at 6am CT"
  schedule         = "0 11 * * *"
  time_zone        = "America/Chicago"
  attempt_deadline = "600s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/psa-${var.environment}-daily-reference-job:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}

resource "google_cloud_run_v2_job" "daily_reference" {
  name                = "psa-${var.environment}-daily-reference-job"
  location            = var.region
  project             = var.project_id
  deletion_protection = false

  template {
    template {
      containers {
        image   = "${var.repository_url}/reference:${var.image_tag}"
        command = ["/usr/local/bin/python3", "-m", "app.reference"]
        env {
          name  = "GCS_BUCKET"
          value = var.bucket_name
        }
        resources {
          limits = {
            memory = "512Mi"
          }
        }
      }
      timeout         = "600s"
      service_account = var.service_account_email
    }
  }
}
