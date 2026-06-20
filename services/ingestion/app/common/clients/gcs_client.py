import logging
from functools import lru_cache

from google.cloud import storage
from pandas import DataFrame

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


def upload_dataframe_to_gcs(
    bucket_name: str, destination_blob_name: str, data: DataFrame
) -> None:
    """Uploads data to a GCS bucket."""
    try:
        storage_client = __get_storage_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        # Write the DataFrame in chunks to avoid memory issues with large datasets
        with blob.open("w", content_type="text/csv") as f:
            data.to_csv(f, index=False)
    except Exception as e:
        logger.error(f"Error uploading to GCS bucket {bucket_name}: {e}")
        raise
