# API Contracts

## Inference Service (FastAPI)

Base URL: Internal Cloud Run service URL (not publicly accessible).

### `POST /predict`

Accepts a game state and returns probability distributions from the four-model chain.

**Request:**
```json
{
  "pitcherId": "string",
  "batterId": "string",
  "balls": 0,
  "strikes": 0,
  "outs": 0,
  "runners": 0,
  "inning": 1,
  "inningHalf": "top",
  "homeScore": 0,
  "awayScore": 0,
  "pitcherPitchCount": 0,
  "pitchSequence": [
    {
      "pitchType": "FF",
      "velocity": 95.2,
      "zone": 5,
      "result": "called_strike"
    }
  ]
}
```

**Response (200):**
```json
{
  "nextPitch": {
    "probabilities": { "FF": 0.45, "SL": 0.30, "CH": 0.25 },
    "expectedVelocity": 94.8,
    "expectedZone": 5
  },
  "swingProbability": 0.62,
  "contactQuality": {
    "probabilities": { "weak": 0.3, "medium": 0.4, "hard": 0.3 }
  },
  "predictedOutcome": {
    "probabilities": { "ball": 0.35, "strike": 0.25, "out": 0.20, "single": 0.12, "extra_bases": 0.08 }
  },
  "modelVersions": {
    "nextPitch": "v1.2.0",
    "swing": "v1.1.0",
    "contact": "v1.0.0",
    "outcome": "v1.0.0"
  }
}
```

**Error Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "pitcherId"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### `GET /health`

**Response (200):**
```json
{
  "status": "healthy",
  "modelsLoaded": true,
  "modelVersions": {
    "nextPitch": "v1.2.0",
    "swing": "v1.1.0",
    "contact": "v1.0.0",
    "outcome": "v1.0.0"
  }
}
```

---

## Orchestrator Service (NestJS)

Base URL: Public Cloud Run service URL.

### `GET /events/live/{gameId}`

SSE endpoint for real-time predictions. Returns a stream of `prediction` and `gameState` events.

**Headers:**
```
Accept: text/event-stream
```

**Response (200 — SSE stream):**
```
event: gameState
data: {"gameId":"717251","homeScore":2,"awayScore":1,"inning":5,"inningHalf":"bottom","outs":1,"runners":2,"status":"live"}

event: prediction
data: {"gameId":"717251","atBatId":"abc123","timestamp":"2025-07-15T20:30:00Z","nextPitch":{"probabilities":{"FF":0.45},"expectedVelocity":94.8,"expectedZone":5},"swingProbability":0.62,"contactQuality":{"probabilities":{"weak":0.3,"medium":0.4,"hard":0.3}},"predictedOutcome":{"probabilities":{"ball":0.35,"strike":0.25,"out":0.20,"single":0.12,"extra_bases":0.08}}}
```

### `POST /analyze`

Static analysis endpoint. Accepts a user-defined game state and returns a prediction.

**Request:**
```json
{
  "pitcherId": "string",
  "batterId": "string",
  "balls": 1,
  "strikes": 2,
  "outs": 1,
  "runners": 2,
  "inning": 7,
  "inningHalf": "bottom",
  "homeScore": 3,
  "awayScore": 2,
  "pitcherPitchCount": 87,
  "pitchSequence": [
    { "pitchType": "FF", "velocity": 94.1, "zone": 9, "result": "ball" },
    { "pitchType": "SL", "velocity": 86.3, "zone": 14, "result": "called_strike" },
    { "pitchType": "FF", "velocity": 95.0, "zone": 2, "result": "foul" }
  ]
}
```

**Response (200):** Same shape as `POST /predict` response from the inference service.

### `GET /health`

**Response (200):**
```json
{
  "status": "healthy",
  "firestoreConnected": true,
  "inferenceServiceHealthy": true,
  "activeConnections": 42
}
```
