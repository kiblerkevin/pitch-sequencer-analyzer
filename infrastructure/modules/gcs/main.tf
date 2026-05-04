variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "environment" {
  type = string
}

# checkov:skip=CKV_GCP_62:Logs bucket does not need access logging (circular dependency)
# checkov:skip=CKV_GCP_78:Logs bucket does not need versioning - logs are ephemeral and auto-deleted after 90 days
resource "google_storage_bucket" "access_logs" {
  name          = "psa-${var.environment}-access-logs-${var.project_id}"
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "data_lake" {
  name          = "psa-${var.environment}-data-lake-${var.project_id}"
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  logging {
    log_bucket = google_storage_bucket.access_logs.name
  }

  lifecycle_rule {
    condition {
      age                   = 14
      matches_prefix        = ["raw/"]
      matches_storage_class = ["STANDARD"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

output "bucket_name" {
  value = google_storage_bucket.data_lake.name
}
