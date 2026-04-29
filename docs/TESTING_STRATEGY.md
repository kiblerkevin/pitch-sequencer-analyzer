# Testing Strategy

## Overview
Each service has its own test suite. Tests run in CI on every PR via GitHub Actions.

## Per-Service Testing

### Frontend (Next.js)
- **Framework:** Vitest + React Testing Library
- **Unit tests:** Component rendering, event handlers, state management.
- **Integration tests:** SSE subscription behavior using mock EventSource.
- **No E2E tests in CI.** Manual E2E testing against staging environment.

### Orchestrator (NestJS)
- **Framework:** Jest (built into NestJS)
- **Unit tests:** Cache logic, game state hashing, SSE event formatting.
- **Integration tests:** Full request lifecycle with mocked Firestore and inference service.
- **Mocking:**
  - Firestore: Use `@google-cloud/firestore` mock or in-memory stub that emits onSnapshot events.
  - Inference service: Mock HTTP client returning fixture prediction responses.

### Inference Service (FastAPI)
- **Framework:** pytest
- **Unit tests:** Feature engineering functions, individual model predictions with fixture data.
- **Integration tests:** Full `/predict` endpoint with test model artifacts.
- **Mocking:**
  - GCS: Use `unittest.mock.patch` on the GCS client. Load test model artifacts from a local `tests/fixtures/` directory.
  - Models: Use small, pre-trained test models saved as fixtures.

### Ingestion (Cloud Function)
- **Framework:** pytest
- **Unit tests:** Data extraction and transformation logic.
- **Integration tests:** Full function execution with mocked pybaseball, Firestore, and Pub/Sub clients.
- **Mocking:**
  - pybaseball: Mock API responses with fixture JSON files.
  - Firestore/Pub/Sub: Use `unittest.mock.patch`.

## Coverage Expectations
- Minimum 80% line coverage per service.
- 100% coverage on data transformation and feature engineering functions.
- Coverage reports generated in CI and posted to PR comments.

## Test Data
- Store test fixtures in `tests/fixtures/` within each service directory.
- Use realistic but anonymized game data.
- Never use live API calls in tests.

## CI Integration
See [CI_CD.md](./CI_CD.md) for how tests are executed in the GitHub Actions pipeline.
