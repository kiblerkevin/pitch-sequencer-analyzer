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
