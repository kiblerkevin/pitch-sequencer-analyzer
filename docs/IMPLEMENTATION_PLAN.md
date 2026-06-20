# Implementation Plan

This document breaks the PLAN.md roadmap into concrete implementation tasks with acceptance criteria, dependencies, and estimated effort. Each phase must be fully complete before starting the next.

Effort estimates assume a small team of contributors working part-time.

---

## Phase 1: Project Scaffolding & Infrastructure Foundation

**Goal:** Monorepo structure, CI pipeline, and base GCP infrastructure are operational.

**Estimated effort:** 1–2 weeks

### 1.1 Monorepo Setup
- [ ] Initialize monorepo root with shared `.gitignore`, `.editorconfig`, and root `package.json` (for workspace scripts).
- [ ] Create service directories: `services/frontend/`, `services/orchestrator/`, `services/inference/`, `services/ingestion/`.
- [ ] Scaffold each service with its package manager config:
  - `services/frontend/` — `npx create-next-app` with TypeScript, Tailwind, App Router.
  - `services/orchestrator/` — `nest new` with TypeScript.
  - `services/inference/` — `requirements.txt`, FastAPI app skeleton, Dockerfile.
  - `services/ingestion/` — `requirements.txt`, Cloud Function entry point, Dockerfile.
- [ ] Add `.env.example` files per service (see [RUNBOOK.md](./RUNBOOK.md)).
- [ ] Add a Dockerfile to each service.

**Acceptance criteria:** Each service starts locally and responds on its health endpoint. `docker build` succeeds for all four services.

### 1.2 Linting & Formatting
- [ ] Configure ESLint + Prettier for `frontend/` and `orchestrator/` with shared config.
- [ ] Configure Ruff for `inference/` and `ingestion/`.
- [ ] Add `lint` and `format` scripts to each service.

**Acceptance criteria:** `lint` and `format` commands pass with zero errors on the scaffolded code.

### 1.3 CI Pipeline
- [ ] Create `.github/workflows/ci.yml`:
  - Path-filter-based change detection per service.
  - Lint & format check.
  - Test (placeholder — no tests yet).
  - Docker build (no push).
- [ ] Create `.github/workflows/infra-plan.yml`:
  - Triggers on `infrastructure/` changes.
  - Runs `tofu init` and `tofu plan`.
  - Posts plan output as PR comment.

**Acceptance criteria:** A PR touching any service triggers only that service's CI jobs. Infra plan runs and posts output on infra changes.

### 1.4 Base GCP Infrastructure (OpenTofu)
- [ ] Create OpenTofu modules per [INFRASTRUCTURE.md](./INFRASTRUCTURE.md):
  - `modules/gcs/` — Data lake bucket with lifecycle policy (Nearline after 14 days).
  - `modules/firestore/` — Firestore database in Native mode.
  - `modules/pubsub/` — `pitch-data-raw` topic and GCS subscriber.
  - `modules/iam/` — Service accounts for ingestion, orchestrator, inference.
  - `modules/secrets/` — Secret Manager secret placeholders.
- [ ] Create `environments/dev/` configuration referencing the modules.
- [ ] Configure GCS remote state backend (`backend.tf`).
- [ ] Apply to dev environment and verify resources exist.

**Acceptance criteria:** `tofu apply` for dev succeeds. GCS bucket, Firestore database, Pub/Sub topic, service accounts, and Secret Manager secrets exist in the GCP project.

---

## Phase 2: Data Ingestion Pipeline

**Goal:** Live game data flows into Firestore and the data lake. Historical data is loaded for model training.

**Estimated effort:** 2–3 weeks

**Depends on:** Phase 1 complete.

### 2.1 Historical Data Backfill (Cloud Run Job)
- [ ] Create `services/ingestion/app/backfill.py` entry point:
  - Uses `pybaseball.statcast()` to pull historical pitch data by year.
  - Accepts `START_YEAR` and `END_YEAR` environment variables (default: last 3 years).
  - Writes CSV files to `gs://{bucket}/historical/{YYYY}/statcast_{YYYY}.csv`.
  - Logs progress per year (structured JSON).
- [ ] Create a separate Dockerfile target or entry point for the backfill job:
  - `CMD ["python", "-m", "app.backfill"]`
- [ ] Add OpenTofu module `modules/cloud-run-job/` for the backfill:
  - Cloud Run Job (not a service — runs to completion).
  - Uses the ingestion service account (GCS write only).
  - No Cloud Scheduler — triggered manually via console, gcloud, or GitHub Actions.
  - Timeout: 30 minutes.
  - Memory: 2Gi (Statcast DataFrames are large).
- [ ] Add a `workflow_dispatch` GitHub Actions workflow to trigger the backfill job on demand.
- [ ] Run backfill against dev environment and verify data in GCS.

**Acceptance criteria:** 3 years of Statcast CSVs are in the data lake. Files are readable and contain expected columns (pitch type, velocity, zone, outcome, batter/pitcher IDs, game state fields). Job completes within 30 minutes.

### 2.2 Live Ingestion Function
- [ ] Create `services/ingestion/app/live.py` entry point:
  - Uses `pybaseball` / MLB Stats API to fetch current game state.
  - Detects if a Cubs game is active. No-ops if no active game.
  - Dual-write:
    - Publishes raw JSON to `pitch-data-raw` Pub/Sub topic.
    - Extracts current play state and writes to `games/{gameId}` and `games/{gameId}/atBats/{atBatId}` in Firestore (see [DATA_MODELS.md](./DATA_MODELS.md)).
- [ ] Implement idempotency — duplicate polls for the same pitch should not create duplicate Firestore documents.
- [ ] Create shared utilities in `services/ingestion/app/common/`:
  - GCS client wrapper.
  - Firestore client wrapper.
  - Pub/Sub client wrapper.
  - Structured logging setup.

**Acceptance criteria:** During a live Cubs game, Firestore documents update every 15 seconds with current game and at-bat state. Raw JSON appears in GCS under `raw/{YYYY}/{MM}/{DD}/{gameId}/`.

### 2.3 Cloud Scheduler & Pub/Sub Subscriber
- [ ] Add OpenTofu modules:
  - `modules/scheduler/` — Cloud Scheduler job triggering the live ingestion function every 15 seconds.
  - `modules/cloud-function/` — Deploy the live ingestion function.
- [ ] Implement Pub/Sub subscriber Cloud Function that writes raw JSON from the topic to GCS.
- [ ] Deploy to dev and run end-to-end during a live game (or with fixture data).

**Acceptance criteria:** Cloud Scheduler triggers the function on schedule. Pub/Sub messages are consumed and raw JSON lands in GCS. No duplicate writes.

### 2.4 Ingestion Tests
- [ ] Unit tests for data extraction and transformation logic (shared by both entry points).
- [ ] Integration tests for live ingestion with mocked pybaseball responses, Firestore emulator, and Pub/Sub emulator.
- [ ] Integration tests for backfill with mocked pybaseball responses and mocked GCS client.
- [ ] Add test fixtures in `services/ingestion/tests/fixtures/`.

**Acceptance criteria:** 80%+ line coverage. Tests pass in CI.

---

## Phase 3: Model Development & Training

**Goal:** Four-model chain is trained, validated, and stored in the model registry.

**Estimated effort:** 3–4 weeks

**Depends on:** Phase 2.1 (historical data) complete. Can overlap with Phase 2.2–2.4.

### 3.1 Feature Engineering Pipeline
- [ ] Create `services/inference/features/` module with feature extraction functions:
  - Game state features: count pressure, baserunners bitmask, fatigue factor, score leverage.
  - Pitcher sequencing features: pitch type/velocity history, location, tendencies.
  - Batter tendency features: hitter profile, pitch-specific tendencies, plate discipline.
- [ ] Build a pipeline that reads historical CSVs from GCS and produces a feature matrix.
- [ ] Unit test each feature function with known inputs/outputs.

**Acceptance criteria:** Feature pipeline produces a DataFrame with all expected columns from raw Statcast data. All feature functions have unit tests.

### 3.2 Model Training
- [ ] Train the four-model chain locally:
  1. Next Pitch Model — predicts pitch type, velocity, location.
  2. Batter Swing Model — predicts swing probability given expected pitch.
  3. Contact Quality Model — predicts contact quality given expected pitch + swing.
  4. Predicted Outcome Model — predicts game outcome given upstream outputs + game state.
- [ ] Use XGBoost (or Random Forest as baseline) with scikit-learn compatible API.
- [ ] Validate with TimeSeriesSplit cross-validation.
- [ ] Log metrics: accuracy, F1 (macro), confusion matrix per model.

**Acceptance criteria:** All four models train successfully. Cross-validation metrics are documented. Models are serialized as `.joblib` files.

### 3.3 Model Registry
- [ ] Upload trained models to `gs://{bucket}/models/{model_name}/v1/model.joblib`.
- [ ] Write `metadata.json` alongside each model with: version, training date, metrics, feature list, training data date range.
- [ ] Create a utility script to upload/download models from the registry.

**Acceptance criteria:** Models and metadata are in GCS. The inference service can download and load them.

### 3.4 Automated Weekly Retraining
- [ ] Create a Vertex AI custom training job (or Cloud Function) that:
  - Pulls latest data from the data lake.
  - Reruns the feature pipeline and training.
  - Uploads new model version to the registry.
- [ ] Add OpenTofu module for the training job schedule (Cloud Scheduler trigger).
- [ ] Add a model version comparison step — only promote if new model metrics meet or exceed the previous version.

**Acceptance criteria:** Weekly job runs, trains new models, and uploads to the registry. Old versions are preserved. Metrics are logged.

---

## Phase 4: Inference Service

**Goal:** FastAPI service serves predictions from the model chain.

**Estimated effort:** 2 weeks

**Depends on:** Phase 3.2 and 3.3 complete.

### 4.1 FastAPI Service
- [ ] Implement model loading on startup via `lifespan` context manager:
  - Downloads latest model artifacts from GCS model registry.
  - Loads all four models into memory.
- [ ] Implement `POST /predict` endpoint per [API_CONTRACTS.md](./API_CONTRACTS.md):
  - Accepts game state request body.
  - Runs feature engineering on the input.
  - Executes the four-model chain sequentially.
  - Returns probability distributions.
- [ ] Implement `GET /health` endpoint returning model versions and load status.

**Acceptance criteria:** `/predict` returns valid probability distributions for a sample game state. `/health` reports loaded model versions. Response time < 500ms.

### 4.2 Cloud Run Deployment
- [ ] Add OpenTofu `modules/cloud-run/` configuration for the inference service:
  - Internal-only ingress.
  - IAM: only the orchestrator service account can invoke.
  - GCS read permission for model artifacts.
  - Scale to zero when idle.
- [ ] Deploy to dev and verify end-to-end with a curl request from the orchestrator's service account.

**Acceptance criteria:** Inference service is deployed to Cloud Run. Only the orchestrator can reach it. Cold start + prediction < 5 seconds.

### 4.3 Inference Tests
- [ ] Unit tests for feature engineering and model chain execution with fixture data.
- [ ] Integration tests for the `/predict` endpoint with small test models.
- [ ] Add test model fixtures in `services/inference/tests/fixtures/models/`.

**Acceptance criteria:** 80%+ line coverage. Tests pass in CI.

---

## Phase 5: Orchestration Layer

**Goal:** NestJS orchestrator connects Firestore, inference, and clients via SSE.

**Estimated effort:** 2–3 weeks

**Depends on:** Phase 4 complete. Phase 2.2 complete (Firestore has live data).

### 5.1 Firestore Listener & Cache
- [ ] Implement Firestore onSnapshot listener for `games/{gameId}/atBats/{atBatId}`.
  - Detect new/changed at-bat documents.
  - Hash the game state to produce a cache key.
- [ ] Implement in-memory LRU cache (e.g., `lru-cache` npm package):
  - TTL: 60 seconds.
  - Max entries: 100.
  - On cache miss: call inference service `/predict`.
  - On cache hit: return cached prediction.

**Acceptance criteria:** Orchestrator logs show Firestore listener receiving updates. Cache hit/miss ratio is logged. Inference service is only called on cache misses.

### 5.2 SSE Broadcast
- [ ] Implement `GET /events/live/{gameId}` SSE endpoint per [API_CONTRACTS.md](./API_CONTRACTS.md):
  - Registers client connection.
  - Sends `gameState` events on Firestore updates.
  - Sends `prediction` events after inference (or cache hit).
  - Handles client disconnection and cleanup.
- [ ] Implement connection tracking (active connection count for health endpoint).

**Acceptance criteria:** Multiple browser tabs can connect to the SSE endpoint and receive synchronized updates. Disconnected clients are cleaned up. `/health` reports active connection count.

### 5.3 Static Analysis Endpoint
- [ ] Implement `POST /analyze` endpoint per [API_CONTRACTS.md](./API_CONTRACTS.md):
  - Accepts user-defined game state.
  - Calls inference service directly (no cache — user inputs are unique).
  - Returns prediction.
- [ ] Design the endpoint to be auth-agnostic — use a middleware slot where authentication can be added later without changing the handler logic.

**Acceptance criteria:** `/analyze` returns predictions for arbitrary game states. The middleware slot is documented in code comments for future auth integration.

### 5.4 Cloud Run Deployment
- [ ] Add OpenTofu Cloud Run configuration for the orchestrator:
  - Public ingress (serves SSE to browsers).
  - Min 1 instance in prod (maintains Firestore listener and SSE connections).
  - IAM: Cloud Run invoke permission on inference service, Firestore read, Secret Manager read.
- [ ] Deploy to dev and verify SSE stream in a browser.

**Acceptance criteria:** Orchestrator is deployed. SSE connections work from a browser. Inference calls succeed via internal networking.

### 5.5 Orchestrator Tests
- [ ] Unit tests for cache logic, game state hashing, SSE event formatting.
- [ ] Integration tests with mocked Firestore (emulator) and mocked inference HTTP client.

**Acceptance criteria:** 80%+ line coverage. Tests pass in CI.

---

## Phase 6: Real-time Dashboard

**Goal:** Next.js frontend displays live predictions for Cubs games.

**Estimated effort:** 3–4 weeks

**Depends on:** Phase 5 complete.

### 6.1 Layout & Navigation
- [ ] Create app layout with navigation between dashboard and static analysis workbench (workbench page is a placeholder for now).
- [ ] Implement responsive layout with Tailwind.

**Acceptance criteria:** App renders with navigation. Layout is responsive on mobile and desktop.

### 6.2 SSE Client Hook
- [ ] Create a `useGameStream` React hook (client component):
  - Connects to `GET /events/live/{gameId}` via EventSource.
  - Parses `gameState` and `prediction` events.
  - Exposes reactive state to child components.
  - Handles reconnection on disconnect.

**Acceptance criteria:** Hook connects to the orchestrator, receives events, and updates React state. Reconnects automatically after a dropped connection.

### 6.3 Score Bug Component
- [ ] Display: score, inning, inning half, outs, count (balls/strikes).
- [ ] Base runner indicator (diamond graphic with runner dots).
- [ ] Reactive — updates from SSE `gameState` events.

**Acceptance criteria:** Score bug displays accurate game state and updates in real-time.

### 6.4 Strike Zone Heat Map
- [ ] SVG-based strike zone visualization.
- [ ] Render pitch probability heat map from `prediction.nextPitch.probabilities` and `expectedZone`.
- [ ] Color scale indicating probability density.

**Acceptance criteria:** Heat map renders and updates on each new prediction event. Color scale is readable and accessible.

### 6.5 Prediction Display
- [ ] Display next pitch type probabilities (bar chart or ranked list).
- [ ] Display swing probability.
- [ ] Display contact quality distribution.
- [ ] Display predicted outcome probabilities.

**Acceptance criteria:** All four model outputs are displayed and update reactively.

### 6.6 Pitcher & Batter Statistics
- [ ] Display current pitcher stats (name, pitch count, pitch mix).
- [ ] Display current batter stats (name, at-bat history).
- [ ] Source data from `gameState` events.

**Acceptance criteria:** Stats display and update on pitcher/batter changes.

### 6.7 No Active Game State
- [ ] When no Cubs game is active, display next scheduled game date/time and opponent.
- [ ] Display previous game summary if available.

**Acceptance criteria:** App handles the no-game state gracefully instead of showing an empty or broken UI.

### 6.8 Cloud Run Deployment
- [ ] Add OpenTofu Cloud Run configuration for the frontend:
  - Public ingress.
  - Scale to zero when idle.
  - No GCP permissions.
- [ ] Deploy to dev and verify end-to-end.

**Acceptance criteria:** Frontend is deployed and accessible. Real-time updates work end-to-end from ingestion through to the browser.

### 6.9 Frontend Tests
- [ ] Unit tests for components (React Testing Library).
- [ ] Integration test for SSE hook with mock EventSource.

**Acceptance criteria:** 80%+ line coverage on components and hooks. Tests pass in CI.

---

## Phase 7: Static Analysis Workbench

**Goal:** Users can define custom game states and get instant predictions.

**Estimated effort:** 2 weeks

**Depends on:** Phase 6 complete (shared UI components).

### 7.1 Game State Input Form
- [ ] Inputs for: pitcher (dropdown), batter (dropdown), count, outs, runners, inning, score.
- [ ] Pitch sequence builder — add/remove pitches with type, velocity, zone.
- [ ] Form validation.

**Acceptance criteria:** Form captures a complete game state matching the `/analyze` request schema.

### 7.2 Reactive Prediction Flow
- [ ] "Analyze" button triggers `POST /analyze` with the form state.
- [ ] "Reactive flow" toggle — when enabled, any form change immediately triggers an inference call (debounced at 300ms).
- [ ] Display prediction results using the same components from Phase 6.5.

**Acceptance criteria:** Predictions return and display correctly. Reactive mode updates on every input change without overwhelming the API (debounce works).

### 7.3 Auth Middleware Preparation
- [ ] The orchestrator's `/analyze` endpoint already has a middleware slot (Phase 5.3).
- [ ] Add a no-op auth middleware that passes all requests through.
- [ ] Document the integration point for future Firebase Authentication.

**Acceptance criteria:** Middleware is in place and documented. Swapping in real auth requires changing only the middleware implementation, not the endpoint or frontend logic.

### 7.4 Workbench Tests
- [ ] Unit tests for form components and validation.
- [ ] Integration test for the analyze flow with mocked orchestrator response.

**Acceptance criteria:** Tests pass in CI.

---

## Phase 8: Monitoring & Observability

**Goal:** Production-grade logging, alerting, dashboards, and uptime checks.

**Estimated effort:** 1–2 weeks

**Depends on:** Phase 6 complete (services are deployed). Can overlap with Phase 7.

### 8.1 Structured Logging
- [ ] Configure structured JSON logging in all services:
  - TypeScript: Use `nestjs-pino` (orchestrator) and a `pino`-based logger (frontend API routes).
  - Python: Use `structlog` or `python-json-logger` (inference, ingestion).
- [ ] Include correlation fields in all log entries: `gameId`, `atBatId`, `requestId`.
- [ ] Logs automatically ship to Cloud Logging via Cloud Run / Cloud Functions.

**Acceptance criteria:** All service logs appear in Cloud Logging as structured JSON with correlation fields. Logs are filterable by service, severity, and game ID.

### 8.2 Cloud Monitoring Alerts
- [ ] Create alert policies via OpenTofu (`modules/monitoring/`):
  - Cloud Run error rate > 5% over 5 minutes (all services).
  - Cloud Run instance count at max for > 10 minutes (orchestrator).
  - Cloud Function execution errors > 3 consecutive failures (ingestion).
  - Firestore read/write quota > 80%.
  - Inference service latency p95 > 2 seconds.
- [ ] Configure notification channel (email or Slack webhook).

**Acceptance criteria:** Alerts fire correctly when thresholds are breached (test with synthetic errors). Notifications are received.

### 8.3 Uptime Checks
- [ ] Create Cloud Monitoring uptime checks via OpenTofu:
  - Frontend: HTTPS check every 5 minutes.
  - Orchestrator `/health`: HTTPS check every 1 minute.
  - Inference `/health`: Internal check every 5 minutes (via orchestrator health which reports `inferenceServiceHealthy`).
- [ ] Alert on downtime > 5 minutes.

**Acceptance criteria:** Uptime checks are active in Cloud Monitoring. Downtime triggers an alert.

### 8.4 Grafana Cloud Dashboards
- [ ] Set up Grafana Cloud free tier account.
- [ ] Configure Cloud Monitoring as a data source in Grafana (via the GCP Grafana plugin).
- [ ] Create dashboards:
  - **Service Health** — Request rate, error rate, latency (p50/p95/p99) per service.
  - **Ingestion Pipeline** — Polls/minute, Firestore writes/minute, Pub/Sub message backlog.
  - **Inference Performance** — Prediction latency, cache hit ratio, model versions in use.
  - **Real-time Connections** — Active SSE connections, connection churn rate.
  - **Cost Tracking** — Cloud Run instance hours, Firestore read/write counts, GCS operations.

**Acceptance criteria:** Dashboards display live data from the deployed services. All key metrics from the service health, ingestion, inference, and connection panels are populated.

### 8.5 Monitoring Infrastructure as Code
- [ ] Add OpenTofu module `modules/monitoring/` for:
  - Alert policies.
  - Notification channels.
  - Uptime checks.
  - Log-based metrics (if needed for custom Grafana panels).
- [ ] Add Grafana dashboard JSON exports to `docs/grafana/` for version control.

**Acceptance criteria:** All monitoring resources are managed via OpenTofu. Grafana dashboards can be restored from the exported JSON.

---

## Phase 9: Staging & Production Deployment

**Goal:** Full deployment pipeline is operational across all environments.

**Estimated effort:** 1–2 weeks

**Depends on:** All previous phases complete.

### 9.1 Staging Environment
- [ ] Create `infrastructure/environments/staging/` OpenTofu configuration.
- [ ] Create `.github/workflows/deploy-staging.yml` — auto-deploys on merge to `main`.
- [ ] Deploy all services to staging and run end-to-end validation during a live game.

**Acceptance criteria:** Staging environment is fully operational. Data flows from ingestion through to the frontend.

### 9.2 Production Environment
- [ ] Create `infrastructure/environments/prod/` OpenTofu configuration.
  - Orchestrator: min 1 instance.
  - All other services: scale to zero.
- [ ] Create `.github/workflows/deploy-prod.yml` — manual trigger with approval gate.
- [ ] Deploy to production.

**Acceptance criteria:** Production environment is live. Approval gate works. All monitoring and alerting is active.

### 9.3 Deploy Dev Workflow
- [ ] Create `.github/workflows/deploy-dev.yml` — manual trigger, deploys all services to dev.

**Acceptance criteria:** Dev deployment works end-to-end via manual trigger.

---

## Summary

| Phase | Description | Effort | Depends On |
|---|---|---|---|
| 1 | Project Scaffolding & Infrastructure Foundation | 1–2 weeks | — |
| 2 | Data Ingestion Pipeline | 2–3 weeks | Phase 1 |
| 3 | Model Development & Training | 3–4 weeks | Phase 2.1 |
| 4 | Inference Service | 2 weeks | Phase 3.2, 3.3 |
| 5 | Orchestration Layer | 2–3 weeks | Phase 4, Phase 2.2 |
| 6 | Real-time Dashboard | 3–4 weeks | Phase 5 |
| 7 | Static Analysis Workbench | 2 weeks | Phase 6 |
| 8 | Monitoring & Observability | 1–2 weeks | Phase 6 (can overlap Phase 7) |
| 9 | Staging & Production Deployment | 1–2 weeks | All phases |

**Total estimated effort: 17–26 weeks**

**Critical path:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 9

Phases 7 and 8 can run in parallel with each other and partially overlap with Phase 6/9.
