import logging

from app.backfill.clients.pybaseball import fetch_statcast_data
from app.backfill.utilities.arg_parser import parse_args
from app.common.clients.gcs_client import upload_dataframe_to_gcs

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Cloud Run Job entry point for historical Statcast data backfill."""
    args = parse_args()

    start_year = args.start_year
    end_year = args.end_year
    bucket = args.bucket

    if start_year > end_year:
        raise ValueError("Start year must be less than or equal to end year")

    logger.info(
        f"Starting backfill: {start_year}-{end_year} -> gs://{bucket}/historical/"
    )

    failed_years = []

    for year in range(start_year, end_year + 1):
        logger.info(f"Processing year {year}...")
        try:
            data = fetch_statcast_data(f"{year}-01-01", f"{year}-12-31")
            upload_dataframe_to_gcs(
                bucket,
                f"historical/{year}/statcast_{year}.csv",
                data,
            )
        except Exception as e:
            logger.error(f"Error processing year {year}: {e}")
            failed_years.append(year)
            continue

    if failed_years:
        logger.error(f"Failed to process years: {failed_years}")
        raise SystemExit(1)

    logger.info("Backfill process complete.")


if __name__ == "__main__":
    main()
