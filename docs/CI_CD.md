# CI/CD

All pipelines run on GitHub Actions. Deployments target GCP Cloud Run and Cloud Functions.

## Workflow Structure

```
.github/workflows/
├── ci.yml                    # Runs on all PRs
├── deploy-dev.yml            # Manual trigger for dev deployment
├── deploy-staging.yml        # Auto-deploys on merge to main
├── deploy-prod.yml           # Manual trigger with approval gate
└── infra-plan.yml            # OpenTofu plan on infra/ changes
```

## CI Pipeline (`ci.yml`)

Triggers on: Pull request to `main`.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Detect      │────►│  Lint &      │────►│  Test        │────►│  Build       │
│  Changes     │     │  Format      │     │              │     │  (Docker)    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

- **Detect Changes:** Uses path filters to determine which services changed. Only runs downstream jobs for affected services.
- **Lint & Format:** Runs ESLint/Prettier (TypeScript) or Ruff (Python) on changed services.
- **Test:** Runs the test suite for changed services. Posts coverage report to PR.
- **Build:** Builds Docker images to verify they compile. Does not push.

## Deployment Pipeline

### Dev
- Trigger: Manual (`workflow_dispatch`).
- Deploys all services to the dev environment.
- Runs OpenTofu apply for `infrastructure/environments/dev/`.

### Staging
- Trigger: Merge to `main`.
- Builds and pushes Docker images to Artifact Registry.
- Runs OpenTofu apply for `infrastructure/environments/staging/`.
- Deploys updated services to Cloud Run / Cloud Functions.

### Production
- Trigger: Manual (`workflow_dispatch`) with required approval.
- Same steps as staging, targeting `infrastructure/environments/prod/`.
- Requires at least one approval from a team member.

## Infrastructure Pipeline (`infra-plan.yml`)

Triggers on: PR with changes to `infrastructure/`.

- Runs `tofu plan` for all environments.
- Posts the plan output as a PR comment for review.
- Does not apply — apply happens only in deployment workflows.

## Secrets in CI
- GCP service account key stored as a GitHub Actions secret.
- Workload Identity Federation preferred over long-lived keys when possible.
- No secrets are logged or exposed in workflow outputs.

## Docker Images
- One Dockerfile per service in the service directory.
- Images tagged with `{service}:{git-sha}` and `{service}:latest`.
- Pushed to GCP Artifact Registry.
