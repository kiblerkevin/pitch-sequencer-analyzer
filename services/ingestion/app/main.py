import functions_framework
from flask import Request, jsonify


@functions_framework.http
def ingest(request: Request):
    """Cloud Function entry point for pitch data ingestion."""
    # TODO: Implement live polling and backfill mode
    return jsonify({"status": "ok"})


def health():
    return {"status": "healthy"}
