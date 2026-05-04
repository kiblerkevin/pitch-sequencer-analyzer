#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: ./bootstrap.sh pitch-sequence-analyzer"
  exit 1
fi

PROJECT_ID="$1"
BUCKET_NAME="psa-tfstate-${PROJECT_ID}"
REGION="${2:-us-central1}"

echo "Creating state bucket: ${BUCKET_NAME}"
gcloud storage buckets create "gs://${BUCKET_NAME}" \
  --project="${PROJECT_ID}" \
  --location="${REGION}" \
  --uniform-bucket-level-access \
  --public-access-prevention

echo "Enabling versioning on state bucket"
gcloud storage buckets update "gs://${BUCKET_NAME}" --versioning

echo ""
echo "State bucket created. Next steps:"
echo "1. Uncomment the backend block in infrastructure/environments/dev/backend.tf"
echo "2. Replace 'your-gcp-project-id' with '${PROJECT_ID}' in the backend block"
echo "3. Run: cd infrastructure/environments/dev && tofu init"
