# Security

## Principles
- No public access to internal services (inference, Firestore).
- Least-privilege IAM for all service accounts.
- No secrets in code, environment files, or CI logs.
- All inter-service communication over HTTPS.

## Secret Management
- All secrets stored in GCP Secret Manager.
- Secrets referenced at runtime via Secret Manager SDK or Cloud Run secret mounts.
- Secrets required:
  - MLB Stats API key (if applicable).
  - Firestore service account credentials (via Workload Identity where possible).
- Secret rotation: API keys rotated quarterly. Rotation process documented in [RUNBOOK.md](./RUNBOOK.md).

## IAM & Service Accounts

Each service runs under a dedicated service account with minimal permissions.

| Service | Service Account | Permissions |
|---|---|---|
| Ingestion Function | `psa-ingestion@{project}.iam` | Firestore write, Pub/Sub publish, GCS write |
| Orchestrator | `psa-orchestrator@{project}.iam` | Firestore read, Secret Manager read, Cloud Run invoke |
| Inference Service | `psa-inference@{project}.iam` | GCS read (model artifacts) |
| Frontend | None (public Cloud Run) | No GCP permissions |

## Network Security

### Cloud Run
- Inference service: Ingress set to `internal`. Only reachable by the orchestrator via Cloud Run service-to-service auth.
- Orchestrator: Ingress set to `all` (public, serves SSE to browsers). Authenticated calls to inference service use IAM-based auth tokens.
- Frontend: Ingress set to `all` (public).

### Firestore
- No client-side access. All reads/writes go through server-side service accounts.
- Firestore Security Rules deny all client access:
  ```
  rules_version = '2';
  service cloud.firestore {
    match /databases/{database}/documents {
      match /{document=**} {
        allow read, write: if false;
      }
    }
  }
  ```

## Rate Limiting
- Orchestrator exposes a public SSE endpoint. Apply rate limiting at the Cloud Run level or via a middleware in NestJS.
- Limit: 10 SSE connections per IP.
- Static analysis endpoint (`POST /analyze`): 60 requests per minute per IP.

## Data Privacy
- The application processes publicly available MLB game data. No user PII is collected or stored.
- If user accounts are added in the future, implement Firebase Authentication and update Firestore Security Rules accordingly.

## Dependency Security
- Use `npm audit` (TypeScript) and `pip-audit` (Python) in CI to scan for known vulnerabilities.
- Dependabot enabled for automated dependency update PRs.
