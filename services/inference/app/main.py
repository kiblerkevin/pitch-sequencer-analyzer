from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

models: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Load model artifacts from GCS on startup
    models["loaded"] = True
    yield
    models.clear()


app = FastAPI(title="Pitch Sequencer Inference Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "modelsLoaded": models.get("loaded", False),
        "modelVersions": {},
    }
