import logging
from datetime import date, timedelta

from app.backfill.clients.pybaseball import fetch_statcast_data
from app.backfill.utilities.arg_parser import parse_args
from app.common.clients.gcs_client import upload_dataframe_to_gcs

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def _gcs_path(d: date) -> str:
    return f"historical/{d.year}/{d.month:02d}/{d.day:02d}/statcast_{d}.csv"


def _ingest_date(bucket: str, d: date) -> list[date]:
    failed_dates = []
    try:
        date_str = d.isoformat()
        logger.info(f"Processing {date_str}...")
        data = fetch_statcast_data(date_str, date_str)
        upload_dataframe_to_gcs(bucket, _gcs_path(d), data)
    except Exception as e:
        logger.error(f"Failed to ingest data for {d}: {e}")
        failed_dates.append(d)
        raise

    return failed_dates


def main() -> None:
    """Cloud Run Job entry point for historical Statcast data backfill."""
    args = parse_args()
    bucket = args.bucket

    failed_dates = []
    if args.daily:
        yesterday = date.today() - timedelta(days=1)
        logger.info(
            f"Daily ingestion: {yesterday} -> gs://{bucket}/{_gcs_path(yesterday)}"
        )
        failed_dates = _ingest_date(bucket, yesterday)

    elif args.date:
        d = date.fromisoformat(args.date)
        logger.info(f"Single-date ingestion: {d} -> gs://{bucket}/{_gcs_path(d)}")
        failed_dates = _ingest_date(bucket, d)

    else:
        start_year = args.start_year
        end_year = args.end_year
        if end_year is None:
            raise ValueError("--end-year is required with --start-year")
        if start_year > end_year:
            raise ValueError("--start-year must be less than or equal to --end-year")

        logger.info(
            f"Starting backfill: {start_year}-{end_year} -> gs://{bucket}/historical/"
        )

        failed_dates = []
        for year in range(start_year, end_year + 1):
            current = date(year, 1, 1)
            while current <= date(year, 12, 31):
                failed_dates.extend(_ingest_date(bucket, current))
                current += timedelta(days=1)

        if failed_dates:
            logger.error(f"Failed to process dates: {failed_dates}")
            raise SystemExit(1)

    logger.info("Backfill process complete.")


if __name__ == "__main__":
    main()
