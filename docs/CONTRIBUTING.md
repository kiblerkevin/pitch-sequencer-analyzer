# Contributing

## Getting Started
1. Clone the repository.
2. Follow [RUNBOOK.md](./RUNBOOK.md) to set up your local development environment.
3. Create a branch from `main` following the naming conventions below.

## Branch Naming

```
{type}/{short-description}
```

Types:
- `feature/` — New functionality
- `fix/` — Bug fixes
- `infra/` — Infrastructure changes (OpenTofu, CI/CD)
- `docs/` — Documentation only
- `refactor/` — Code changes that don't add features or fix bugs

Examples:
- `feature/sse-broadcast`
- `fix/firestore-listener-reconnect`
- `infra/cloud-run-autoscaling`

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
{type}({scope}): {description}
```

Scopes: `frontend`, `orchestrator`, `inference`, `ingestion`, `infra`, `docs`

Examples:
- `feat(orchestrator): add SSE broadcast endpoint`
- `fix(inference): handle missing pitch sequence`
- `infra(cloud-run): configure min instances`

## Pull Request Process
1. Keep PRs focused — one feature or fix per PR.
2. Ensure all CI checks pass before requesting review.
3. Include a description of what changed and why.
4. Link to the relevant PLAN.md phase or open question if applicable.
5. At least one approval is required before merging.
6. Squash merge into `main`.

## Code Review Expectations
- Review for correctness, security, and adherence to [CODING_STANDARDS.md](./CODING_STANDARDS.md).
- Check that data models match [DATA_MODELS.md](./DATA_MODELS.md) and API contracts match [API_CONTRACTS.md](./API_CONTRACTS.md).
- Verify error handling and logging follow project conventions.
- Flag any hardcoded values that should be environment variables.
