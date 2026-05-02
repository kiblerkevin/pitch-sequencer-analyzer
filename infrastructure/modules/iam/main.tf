variable "project_id" {
  type = string
}

variable "environment" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "pubsub_topic_name" {
  type = string
}

# --- Service Accounts ---

resource "google_service_account" "ingestion" {
  project      = var.project_id
  account_id   = "psa-${var.environment}-ingestion"
  display_name = "PSA Ingestion (${var.environment})"
}

resource "google_service_account" "orchestrator" {
  project      = var.project_id
  account_id   = "psa-${var.environment}-orchestrator"
  display_name = "PSA Orchestrator (${var.environment})"
}

resource "google_service_account" "inference" {
  project      = var.project_id
  account_id   = "psa-${var.environment}-inference"
  display_name = "PSA Inference (${var.environment})"
}

# --- Ingestion: Firestore write, Pub/Sub publish, GCS write ---

resource "google_project_iam_member" "ingestion_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.ingestion.email}"
}

resource "google_pubsub_topic_iam_member" "ingestion_publisher" {
  project = var.project_id
  topic   = var.pubsub_topic_name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.ingestion.email}"
}

resource "google_storage_bucket_iam_member" "ingestion_gcs_writer" {
  bucket = var.bucket_name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.ingestion.email}"
}

# --- Orchestrator: Firestore read, Secret Manager read, Cloud Run invoke ---

resource "google_project_iam_member" "orchestrator_firestore" {
  project = var.project_id
  role    = "roles/datastore.viewer"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_project_iam_member" "orchestrator_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_project_iam_member" "orchestrator_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

# --- Inference: GCS read (model artifacts) ---

resource "google_storage_bucket_iam_member" "inference_gcs_reader" {
  bucket = var.bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.inference.email}"
}

# --- Outputs ---

output "ingestion_service_account_email" {
  value = google_service_account.ingestion.email
}

output "orchestrator_service_account_email" {
  value = google_service_account.orchestrator.email
}

output "inference_service_account_email" {
  value = google_service_account.inference.email
}
