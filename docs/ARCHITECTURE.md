# Architecture

## System Overview

Pitch Sequencer Analyzer is a monorepo containing four services that work together to deliver real-time pitch sequencing predictions for Chicago Cubs games.

```
┌─────────────┐    SSE     ┌──────────────────┐   HTTP    ┌───────────────────┐
│  Next.js UI │◄───────────│  NestJS           │─────────►│  FastAPI           │
│  (Cloud Run)│            │  Orchestrator     │          │  Inference Service │
└─────────────┘            │  (Cloud Run)      │          │  (Cloud Run)       │
                           └────────┬─────────┘          └───────────────────┘
                                    │ onSnapshot                    │
                                    ▼                               │
                           ┌──────────────────┐                     │
                           │    Firestore      │                     │
                           └────────▲─────────┘                     │
                                    │ write                         │
                           ┌────────┴─────────┐          ┌─────────▼─────────┐
                           │  Cloud Function   │          │   GCS Bucket       │
                           │  (Ingestion)      │─────────►│   (Data Lake +     │
                           └────────▲─────────┘  Pub/Sub │    Model Registry) │
                                    │ trigger             └───────────────────┘
                           ┌────────┴─────────┐
                           │  Cloud Scheduler  │
                           └──────────────────┘
```

## Services

### Next.js Frontend (`/services/frontend`)
- Hosts the real-time dashboard and static analysis workbench.
- Subscribes to the orchestrator's SSE endpoint via the browser EventSource API.
- No direct database access.

### NestJS Orchestrator (`/services/orchestrator`)
- Central hub for all client-facing data.
- Holds a single Firestore onSnapshot listener for game state changes.
- Maintains an in-memory LRU cache of inference results keyed by game state hash.
- On cache miss, calls the FastAPI inference service.
- Broadcasts predictions to all connected SSE clients.
- Serves the static analysis workbench API (accepts user-defined game state, calls inference, returns result).

### FastAPI Inference Service (`/services/inference`)
- Stateless prediction service.
- Loads model artifacts from GCS on startup.
- Exposes a `/predict` endpoint that accepts game state and returns probability distributions.
- Runs the four-model chain: Next Pitch → Batter Swing → Contact Quality → Predicted Outcome.

### Cloud Function — Ingestion (`/services/ingestion`)
- Triggered by Cloud Scheduler every 15 seconds during active games.
- Uses pybaseball to poll the MLB Stats API for live game data.
- Dual-write pattern:
  - Publishes raw JSON to Pub/Sub (consumed by a subscriber that writes to GCS).
  - Writes extracted game state to Firestore.

## Communication Patterns

| From | To | Protocol | Purpose |
|---|---|---|---|
| Cloud Scheduler | Cloud Function | HTTP trigger | Poll for new pitch data |
| Cloud Function | Firestore | Firestore SDK | Write current game state |
| Cloud Function | Pub/Sub | Pub/Sub SDK | Publish raw data for lake ingestion |
| Pub/Sub | GCS | Cloud Function subscriber | Store raw JSON in data lake |
| Firestore | Orchestrator | onSnapshot listener | Push game state changes |
| Orchestrator | Inference Service | HTTP (internal) | Request predictions |
| Orchestrator | Frontend | SSE | Broadcast predictions to clients |
| Frontend | Orchestrator | HTTP | Static analysis requests |

## Monorepo Structure

```
/
├── services/
│   ├── frontend/          # Next.js + Tailwind
│   ├── orchestrator/      # NestJS
│   ├── inference/         # FastAPI
│   └── ingestion/         # Cloud Function (Python)
├── infrastructure/        # OpenTofu modules
├── docs/                  # Project documentation
├── .github/workflows/     # CI/CD pipelines
├── PLAN.md
└── README.md
```
