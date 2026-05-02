variable "project_id" {
  type = string
}

variable "environment" {
  type = string
}

resource "google_pubsub_topic" "pitch_data_raw" {
  project = var.project_id
  name    = "psa-${var.environment}-pitch-data-raw"

  message_retention_duration = "86400s"
}

output "topic_name" {
  value = google_pubsub_topic.pitch_data_raw.name
}

output "topic_id" {
  value = google_pubsub_topic.pitch_data_raw.id
}
