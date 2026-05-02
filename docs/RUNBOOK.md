# Runbook

## Prerequisites
- Node.js 24 LTS
- Python 3.12
- npm 10.x (npm 11.x has a known bug where `npm install` skips package extraction)
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
cd services/frontend && NODE_ENV=development npm install && cd ../..

# Orchestrator
cd services/orchestrator && NODE_ENV=development npm install && cd ../..

# Python virtual environment (from project root)
python3 -m venv .venv
source .venv/bin/activate
pip install ruff

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

### NODE_ENV=production in shell
Some IDE extensions (e.g., CodeGPT) set `NODE_ENV=production` globally. This causes `npm install` to skip devDependencies (ESLint, Prettier, TypeScript types, etc.). Always use `NODE_ENV=development npm install` when installing dependencies for TypeScript services.

### __NEXT_PRIVATE_STANDALONE_CONFIG breaks `next build`
Some IDE extensions inject `__NEXT_PRIVATE_STANDALONE_CONFIG` into the environment, which overrides the local Next.js config and causes `TypeError: generate is not a function` during builds. Fix by unsetting it before building:
```bash
env -u __NEXT_PRIVATE_STANDALONE_CONFIG npm run build
```
Alternatively, identify and disable the extension that sets this variable.

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
