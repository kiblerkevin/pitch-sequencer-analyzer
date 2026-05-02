variable "project_id" {
  type = string
}

variable "environment" {
  type = string
}

resource "google_secret_manager_secret" "mlb_api_key" {
  project   = var.project_id
  secret_id = "psa-${var.environment}-mlb-api-key"

  replication {
    auto {}
  }
}

output "mlb_api_key_secret_id" {
  value = google_secret_manager_secret.mlb_api_key.secret_id
}
