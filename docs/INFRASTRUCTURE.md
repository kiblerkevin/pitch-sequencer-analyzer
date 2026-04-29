# Infrastructure

All GCP infrastructure is managed via OpenTofu. No resources are created manually or via gcloud CLI.

## OpenTofu Module Structure

```
infrastructure/
├── modules/
│   ├── cloud-run/           # Reusable module for Cloud Run services
│   ├── cloud-function/      # Reusable module for Cloud Functions
│   ├── firestore/           # Firestore database and indexes
│   ├── gcs/                 # GCS buckets and lifecycle policies
│   ├── pubsub/              # Pub/Sub topics and subscriptions
│   ├── scheduler/           # Cloud Scheduler jobs
│   ├── secrets/             # Secret Manager secrets
│   └── iam/                 # Service accounts and IAM bindings
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
└── backend.tf               # GCS remote state backend config
```

## Naming Conventions

All GCP resources follow this pattern:

```
psa-{environment}-{service}-{resource}
```

Examples:
- `psa-prod-ingestion-fn` (Cloud Function)
- `psa-prod-orchestrator-run` (Cloud Run service)
- `psa-prod-data-lake-bucket` (GCS bucket)
- `psa-prod-pitch-data-raw-topic` (Pub/Sub topic)

## Environments

| Environment | Purpose | Cloud Run Min Instances |
|---|---|---|
| dev | Local development backing services | 0 |
| staging | Pre-production validation | 0 |
| prod | Live application | 1 (orchestrator only) |

## State Management
- Remote state stored in a dedicated GCS bucket: `psa-tfstate-{project_id}`.
- State locking enabled.
- One state file per environment.

## Key Infrastructure Decisions

### Cloud Run
- All services deployed to Cloud Run.
- Orchestrator: min 1 instance in prod (holds SSE connections and Firestore listener).
- Inference and frontend: scale to zero when idle.
- Internal-only networking between orchestrator and inference service.

### GCS Bucket
- Single bucket with prefix-based organization (see [DATA_MODELS.md](./DATA_MODELS.md)).
- Lifecycle policy: move `raw/` objects to Nearline after 14 days.
- Model artifacts in `models/` remain in Standard storage.

### Firestore
- Native mode.
- Composite indexes defined in OpenTofu for query patterns used by the orchestrator.

### IAM
- Least-privilege service accounts per service.
- Ingestion function: Firestore write, Pub/Sub publish, GCS write.
- Orchestrator: Firestore read, Secret Manager read, Cloud Run invoke (inference).
- Inference service: GCS read (model artifacts).
- Frontend: No GCP permissions.
