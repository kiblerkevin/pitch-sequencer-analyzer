# Project Roadmap

## Application Overview
This application will utilize advanced baseball tracking data to determine how a pitcher's sequencing strategy impacts the batter's contact quality and expected outcomes.

Users can follow along in real-time as the application predicts the pitch sequencing and batting outcome for a live at-bat for the Chicago Cubs or Chicago White Sox. On a separate page, the user can use perform a reactive, static analysis on expected batting outcomes by suggesting "what-if" options for pitch sequencing, pitch count, etc.

## Technologies
- Reactive UI
    - Next.js
    - Tailwind
- Orchestration Layer
    - Typescript
- Game State Cache
    - In-memory orchestrator cache (present)
    - Firestore (future state)
- Inference Microservice Layer
    - Python
    - FastAPI
- Model
    - Python
    - Scikit-learn
    - Random Forest Classifier
- Real-time Client Push
    - Server-Sent Events (SSE)
- Data Ingestion
    - Python
- Data Storage
    - Data Lake
        - Bucket
    - Application Database
        - NoSQL
- Cloud Provider
    - Google Cloud Provider
    - OpenTofu

## Real-time Data Flow
- Pitch data is polled from MLB Statcast using pybaseball to scrape the MLB Stats API and Baseball Savant's live feed.
- Ingestion flow publishes a pub/sub message and stores data in Firestore NoSQL database.
- Subscribed data lake ingestion function stores message data in the datalake.
- Orchestrator holds a single Firestore onSnapshot listener for game state changes.
- On state change, orchestrator checks in-memory cache for existing prediction.
- On cache miss, orchestrator calls the inference service and caches the result.
- Orchestrator broadcasts the updated prediction to all connected clients via SSE.
- Next.js frontend subscribes to the orchestrator's SSE endpoint (EventSource API).

## Phase 1: Data Foundation
The goal of this phase is to establish a "source of truth" that is immutable and resilient.

- Data Lake
    - GCS Bucket
    - Lifecycle Management to move objects to "nearline" storage after 14 days to reduce the cost footprint.
    - One-time ingestion of historical data (last 3 years) from Statcast for model training.
- Data Ingestion Pipeline
    - GCP Cloud Function with Cloud Scheduler
    - Use the pybaseball python library to poll for pitch data every 15 seconds during Cubs games.
    - "Dual-write"/Pub-Sub pattern
        - Stream raw JSON to the Data Lake
        - Extract "current play" state into Firestore.

- Open Questions
    - How to structure GCS Bucket for our use-case?
    - How might future features impact our design decisions?

## Phase 2: Model Development & Feature Engineering
The goal of this phase is to transform raw telemetry into a predictive engine.

- Next Pitch Model
    - Game State Features
        - Count pressure (balls and strike, normalized to 0 and 1).
        - Baserunners (bitmask for runners on base).
        - Fatigue Factor (Total pitches thrown in the current game).
        - Score Leverage (run differential).
    - Pitcher Sequencing & Tendency Features
        - Pitch Type and Velocity of previous pitches in the at-bat.
        - Pitch location
        - Pitcher tendencies (percentage of pitches thrown in current situation.)
    - Target Variable
        - Expected pitch characteristics (type, velocity, location)
- Batter Swing Model
    - Input: Expected pitch characteristics
    - Game State Features
        - Count pressure (balls and strike, normalized to 0 and 1).
        - Baserunners (bitmask for runners on base).
        - Fatigue Factor (Total pitches thrown in the current game).
        - Score Leverage (run differential).
    - Batter Tendency features
        - Hitter profile (aggressive, patient, power, contact, etc.).
        - Pitch-specific tendencies.
        - Plate discipline tendencies.
    - Target Variable
        - Expected swing or no swing from the batter.
- Batter Contact Model
    - Input: expected pitch characteristics, expected swing from batter.
    - Batter Tendency Feature
        - Hitter profile
        - Batted ball and power tendencies.
    - Target Variable
        - Expected contact quality
- Predicted outcome model
    - Target variable
        - The game outcome of the play
- Validaiton: Use a TimeSeriesSpplit for cross-validaiton
- Weekly retraining on new data
- Model registry
    - /models/ folder of te GCS bucket.

- Open Questions
    - Are these sufficient ML features for the target variable?
    - How can standard baseball advanced statistics be integrated into our model?

### Phase 3: Inference Service/On-Demand Prediction
The goal of this phase is to operationalize our model for real-time predictions.

- Inference Function
    - Python/FastAPI
    - /predict endpoint takes a game state and returns a probabiity distribution for the next pitch and the expectd outcome.
- Orchestration Layer
    - TypeScript/NestJS
    - Holds a single Firestore onSnapshot listener for game state.
    - Broadcasts predictions to connected clients via SSE.
    - Fetches state from UI for static analysis.
    - API key management (GCP Secret Manager) and rate-limiting compliance.

- Open Questions
    - Are these security features sufficient to protect data privacy and keep our application secure?

### Phase 4: Real-time Dashboard
The goal of this phase is to create an engaging and intuitive user experience.

- Real-time dashboard (Cubs)
    - Live Tracker
        - Subscribes to orchestrator SSE endpoint for real-time updates.
    - Strike Zone SVG
        - Reactive visualization that renders "heat maps" of expected pitch probabilities.
    - Score Bug
        - Display game state (score, base runners, count of balls and strikes)
    - Pitcher Statistics
    - Batter Statistics
    - Display previous and next game data if no games are active.

### Phase 5: Static Analysis Workbench
The goal of this phase is to create an engaging and intuitive user experience.

- Static analysis workbench
    - Inputs to manage game state
    - Inputs to manage pitch sequencing
    - "reactive flow" toggle triggers immediate inference call and updates the UI instantly.