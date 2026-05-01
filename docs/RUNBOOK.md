# Runbook

## Prerequisites
- Node.js 22 LTS
- Python 3.12
- Docker & Docker Compose
- OpenTofu CLI
- GCP CLI (`gcloud`) authenticated to the project
- Firebase Emulator Suite (for local Firestore)

## Local Development Setup

### 1. Clone and install dependencies

```bash
git clone <repository-url>
cd pitch-sequencer-analyzer

# Frontend
cd services/frontend && npm install && cd ../..

# Orchestrator
cd services/orchestrator && npm install && cd ../..

# Inference
cd services/inference && pip install -r requirements.txt && cd ../..

# Ingestion
cd services/ingestion && pip install -r requirements.txt && cd ../..
```

### 2. Start local backing services

```bash
# Start Firestore emulator
firebase emulators:start --only firestore

# Or use Docker Compose (if configured)
docker compose up -d
```

### 3. Environment variables

Each service reads from a `.env` file in its directory. Copy the template and fill in values:

```bash
cp services/frontend/.env.example services/frontend/.env
cp services/orchestrator/.env.example services/orchestrator/.env
cp services/inference/.env.example services/inference/.env
cp services/ingestion/.env.example services/ingestion/.env
```

#### Frontend
| Variable | Description | Example |
|---|---|---|
| `NEXT_PUBLIC_ORCHESTRATOR_URL` | Orchestrator base URL | `http://localhost:3001` |

#### Orchestrator
| Variable | Description | Example |
|---|---|---|
| `FIRESTORE_EMULATOR_HOST` | Firestore emulator address | `localhost:8080` |
| `INFERENCE_SERVICE_URL` | Inference service base URL | `http://localhost:8000` |
| `PORT` | Server port | `3001` |

#### Inference Service
| Variable | Description | Example |
|---|---|---|
| `MODEL_PATH` | Path to model artifacts | `./tests/fixtures/models` |
| `PORT` | Server port | `8000` |

#### Ingestion
| Variable | Description | Example |
|---|---|---|
| `FIRESTORE_EMULATOR_HOST` | Firestore emulator address | `localhost:8080` |
| `GCS_BUCKET` | Target GCS bucket (use emulator or local path) | `psa-dev-data-lake` |
| `PUBSUB_EMULATOR_HOST` | Pub/Sub emulator address | `localhost:8085` |

### 4. Run services

```bash
# Terminal 1 — Frontend
cd services/frontend && npm run dev

# Terminal 2 — Orchestrator
cd services/orchestrator && npm run start:dev

# Terminal 3 — Inference
cd services/inference && uvicorn app.main:app --reload --port 8000

# Terminal 4 — Ingestion (manual trigger)
cd services/ingestion && python -m app.main
```

## Common Troubleshooting

### Firestore emulator not connecting
- Verify `FIRESTORE_EMULATOR_HOST` is set in the service's `.env`.
- Ensure the emulator is running: `firebase emulators:start --only firestore`.

### Inference service fails to load models
- Check `MODEL_PATH` points to valid model artifacts.
- For local dev, use test fixtures: `./tests/fixtures/models`.

### SSE connection drops
- Browser EventSource auto-reconnects. Check orchestrator logs for connection lifecycle events.
- Verify the orchestrator's Firestore listener is active (look for `onSnapshot` log entries).

### Ingestion returns empty data
- pybaseball may return empty results outside of game hours. Use fixture data for local testing.
- Check MLB Stats API availability — it occasionally has maintenance windows.

## Deployment

### Manual deployment to dev
```bash
gh workflow run deploy-dev.yml
```

### Production deployment
```bash
# Requires approval from a team member
gh workflow run deploy-prod.yml
```

See [CI_CD.md](./CI_CD.md) for full pipeline details.
