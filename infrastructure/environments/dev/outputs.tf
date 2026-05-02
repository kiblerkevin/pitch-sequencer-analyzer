output "bucket_name" {
  value = module.gcs.bucket_name
}

output "firestore_database" {
  value = module.firestore.database_name
}

output "pubsub_topic" {
  value = module.pubsub.topic_name
}

output "ingestion_service_account" {
  value = module.iam.ingestion_service_account_email
}

output "orchestrator_service_account" {
  value = module.iam.orchestrator_service_account_email
}

output "inference_service_account" {
  value = module.iam.inference_service_account_email
}

output "mlb_api_key_secret_id" {
  value = module.secrets.mlb_api_key_secret_id
}
