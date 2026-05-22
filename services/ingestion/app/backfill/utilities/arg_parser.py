import argparse


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the backfill job."""
    parser = argparse.ArgumentParser(description="Backfill historical Statcast data")
    parser.add_argument(
        "--start-year", type=int, default=2022, help="Start year for backfill"
    )
    parser.add_argument(
        "--end-year", type=int, default=2024, help="End year for backfill"
    )
    parser.add_argument(
        "--bucket", type=str, required=True, help="GCS bucket for output"
    )

    return parser.parse_args()
