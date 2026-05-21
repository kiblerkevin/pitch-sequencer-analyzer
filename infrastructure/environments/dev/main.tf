module "gcs" {
  source = "../../modules/gcs"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

module "firestore" {
  source = "../../modules/firestore"

  project_id = var.project_id
  region     = var.region
}

module "pubsub" {
  source = "../../modules/pubsub"

  project_id  = var.project_id
  environment = var.environment
}

module "iam" {
  source = "../../modules/iam"

  project_id        = var.project_id
  environment       = var.environment
  bucket_name       = module.gcs.bucket_name
  pubsub_topic_name = module.pubsub.topic_name
}

module "secrets" {
  source = "../../modules/secrets"

  project_id  = var.project_id
  environment = var.environment
}

module "workload_identity" {
  source = "../../modules/workload-identity"

  project_id     = var.project_id
  project_number = var.project_number
  environment    = var.environment
  github_repo    = var.github_repo
}

module "artifact_registry_repository" {
  source = "../../modules/artifact-registry-repository"

  project_id     = var.project_id
  region         = var.region
  environment    = var.environment
  immutable_tags = false
}

module "cloud_run_job" {
  source = "../../modules/cloud-run-job"

  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  bucket_name           = module.gcs.bucket_name
  repository_url        = module.artifact_registry_repository.repository_url
  service_account_email = module.iam.ingestion_service_account_email
}
