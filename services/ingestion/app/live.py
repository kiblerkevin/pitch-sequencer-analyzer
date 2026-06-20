import functions_framework
from flask import Request, jsonify


@functions_framework.http
def ingest(request: Request):
    """Cloud Function entry point for live pitch data ingestion."""
    # TODO: Implement live polling via pybaseball/MLB Stats API
    # TODO: Dual-write to Firestore + Pub/Sub
    return jsonify({"status": "ok"})
