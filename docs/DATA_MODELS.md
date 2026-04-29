# Data Models

## Firestore Collections

### `games/{gameId}`
Represents the current state of an active game.

```typescript
interface GameDocument {
  gameId: string;              // MLB game ID
  homeTeam: string;
  awayTeam: string;
  homeScore: number;
  awayScore: number;
  inning: number;
  inningHalf: "top" | "bottom";
  status: "pre" | "live" | "final";
  updatedAt: Timestamp;
}
```

### `games/{gameId}/atBats/{atBatId}`
Represents the current at-bat within a game.

```typescript
interface AtBatDocument {
  atBatId: string;
  pitcherId: string;
  pitcherName: string;
  batterId: string;
  batterName: string;
  balls: number;
  strikes: number;
  outs: number;
  runners: number;             // Bitmask: 0b000 (empty) to 0b111 (loaded)
  pitchSequence: PitchEvent[];
  updatedAt: Timestamp;
}

interface PitchEvent {
  pitchNumber: number;
  pitchType: string;           // e.g. "FF", "SL", "CH", "CU"
  velocity: number;
  zone: number;                // MLB zone 1-14
  result: string;              // e.g. "called_strike", "ball", "foul", "in_play"
}
```

## GCS Bucket Structure

```
gs://pitch-sequencer-data/
├── raw/                       # Raw JSON from MLB Stats API
│   └── {YYYY}/{MM}/{DD}/
│       └── {gameId}/
│           └── {timestamp}.json
├── historical/                # Bulk Statcast CSVs for training
│   └── {YYYY}/
│       └── statcast_{YYYY}.csv
└── models/                    # Model registry
    └── {model_name}/
        └── {version}/
            ├── model.joblib
            └── metadata.json
```

## Pub/Sub Message Schema

### Topic: `pitch-data-raw`

```json
{
  "gameId": "string",
  "timestamp": "ISO 8601",
  "payload": {
    "// Raw MLB Stats API response for the current play"
  }
}
```

## SSE Event Payloads

### Event: `prediction`
Sent by the orchestrator when a new prediction is available.

```typescript
interface PredictionEvent {
  gameId: string;
  atBatId: string;
  timestamp: string;
  nextPitch: {
    probabilities: Record<string, number>;  // e.g. { "FF": 0.45, "SL": 0.30, "CH": 0.25 }
    expectedVelocity: number;
    expectedZone: number;
  };
  swingProbability: number;
  contactQuality: {
    probabilities: Record<string, number>;  // e.g. { "weak": 0.3, "medium": 0.4, "hard": 0.3 }
  };
  predictedOutcome: {
    probabilities: Record<string, number>;  // e.g. { "ball": 0.35, "strike": 0.25, "out": 0.20, "single": 0.12, "extra_bases": 0.08 }
  };
}
```

### Event: `gameState`
Sent by the orchestrator when game state changes without a new prediction (e.g., between at-bats).

```typescript
interface GameStateEvent {
  gameId: string;
  homeScore: number;
  awayScore: number;
  inning: number;
  inningHalf: "top" | "bottom";
  outs: number;
  runners: number;
  status: "pre" | "live" | "final";
}
```

## Inference Service Request/Response

See [API_CONTRACTS.md](./API_CONTRACTS.md) for the full `/predict` endpoint specification.
