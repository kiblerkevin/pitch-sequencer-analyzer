import json
import logging
from functools import lru_cache

from google.cloud import storage
from pandas import DataFrame
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def __get_storage_client() -> storage.Client:
    """Lazily initializes and caches the GCS storage client."""
    try:
        client = storage.Client()
        return client
    except Exception as e:
        logger.error(f"Error initializing GCS storage client: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30), before_sleep=before_sleep_log(logger, logging.WARNING))
def upload_json_to_gcs(bucket_name: str, destination_blob_name: str, data: list | dict) -> None:
    """Uploads a JSON-serializable object to a GCS bucket."""
    try:
        storage_client = __get_storage_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(json.dumps(data), content_type="application/json")
        logger.info("GCS JSON upload completed", extra={"bucket": bucket_name, "destination": destination_blob_name})
    except Exception:
        logger.exception("GCS JSON upload failed", extra={"bucket": bucket_name, "destination": destination_blob_name})
        raise


def download_json_from_gcs(bucket_name: str, blob_name: str) -> list | dict | None:
    """Downloads and deserializes a JSON object from GCS. Returns None if the blob does not exist."""
    try:
        storage_client = __get_storage_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return None
        return json.loads(blob.download_as_text())
    except Exception:
        logger.exception("GCS JSON download failed", extra={"bucket": bucket_name, "blob": blob_name})
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30), before_sleep=before_sleep_log(logger, logging.WARNING))
def upload_dataframe_to_gcs(
    bucket_name: str, destination_blob_name: str, data: DataFrame
) -> None:
    """Uploads data to a GCS bucket."""
    try:
        logger.info(
            "Uploading dataframe to GCS",
            extra={"bucket": bucket_name, "destination": destination_blob_name, "rows": len(data) if data is not None else None},
        )
        storage_client = __get_storage_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        # Write the DataFrame in chunks to avoid memory issues with large datasets
        with blob.open("w", content_type="text/csv") as f:
            data.to_csv(f, index=False)
        logger.info(
            "GCS upload completed",
            extra={"bucket": bucket_name, "destination": destination_blob_name},
        )
    except Exception:
        logger.exception(
            "GCS upload failed",
            extra={"bucket": bucket_name, "destination": destination_blob_name},
        )
        raise
