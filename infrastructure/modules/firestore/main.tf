variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

resource "google_firestore_database" "main" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

output "database_name" {
  value = google_firestore_database.main.name
}
