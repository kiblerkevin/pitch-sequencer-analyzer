import argparse
import os


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MLB data ingestion job")
    parser.add_argument(
        "--bucket", type=str, default=os.environ.get("GCS_BUCKET"), help="GCS bucket for output"
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--daily", action="store_true", help="Ingest yesterday's data")
    mode.add_argument("--date", type=str, help="Ingest a specific date (YYYY-MM-DD)")
    mode.add_argument("--start-year", type=int, help="Start year for multi-year backfill")

    parser.add_argument(
        "--end-year",
        type=int,
        help="End year for multi-year backfill (required with --start-year)",
    )

    return parser.parse_args()
