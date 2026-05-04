# Uncomment after running bootstrap.sh to create the state bucket.

terraform {
  backend "gcs" {
    bucket = "psa-tfstate-pitch-sequence-analyzer"
    prefix = "env/dev"
  }
}
