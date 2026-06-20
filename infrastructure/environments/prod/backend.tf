terraform {
  backend "gcs" {
    bucket = "psa-tfstate-pitch-sequence-analyzer"
    prefix = "env/prod"
  }
}
