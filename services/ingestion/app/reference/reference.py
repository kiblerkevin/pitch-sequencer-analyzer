import logging
from datetime import date, timedelta

from app.common.clients.mlb_stats import fetch_all_players, fetch_schedule, fetch_umpires_for_game, _OFFICIAL_GAME_TYPES
from app.common.utilities.arg_parser import parse_args
from app.common.clients.gcs_client import download_json_from_gcs, upload_json_to_gcs

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

_PLAYERS_PATH = "reference/players/players.json"
_PLAYERS_MANIFEST = "reference/players/manifest.json"
_UMPIRES_MANIFEST = "reference/umpires/manifest.json"
_SCHEDULE_MANIFEST = "reference/schedule/manifest.json"


def _umpire_path(d: date) -> str:
    return f"reference/umpires/{d.year}/{d.month:02d}/{d.day:02d}/umpires.json"


def _schedule_path(year: int) -> str:
    return f"reference/schedule/{year}/schedule.json"


def _ingest_players(bucket: str) -> None:
    players = fetch_all_players()
    upload_json_to_gcs(bucket, _PLAYERS_PATH, players)
    upload_json_to_gcs(bucket, _PLAYERS_MANIFEST, {"count": len(players), "last_updated": date.today().isoformat()})
    logger.info("Players ingestion complete", extra={"count": len(players)})


def _ingest_umpires(bucket: str, start_year: int, end_year: int) -> None:
    manifest = download_json_from_gcs(bucket, _UMPIRES_MANIFEST) or {}
    processed_pks = set(manifest.get("processed_game_pks", []))

    failed_game_pks = []
    processed = 0
    for year in range(start_year, end_year + 1):
        games = fetch_schedule(date(year, 1, 1), date(year, 12, 31), game_types=_OFFICIAL_GAME_TYPES)
        for game in games:
            game_pk = game["gamePk"]
            if game_pk in processed_pks:
                continue
            game_date = date.fromisoformat(game["officialDate"])
            try:
                umpire = fetch_umpires_for_game(game_pk)
                if umpire:
                    existing = download_json_from_gcs(bucket, _umpire_path(game_date)) or []
                    existing.append(umpire)
                    upload_json_to_gcs(bucket, _umpire_path(game_date), existing)
                    processed_pks.add(game_pk)
                    processed += 1
            except Exception:
                logger.exception("Failed to ingest umpire data", extra={"game_pk": game_pk})
                failed_game_pks.append(game_pk)

    upload_json_to_gcs(bucket, _UMPIRES_MANIFEST, {
        "processed_game_pks": sorted(processed_pks),
        "last_updated": date.today().isoformat(),
    })
    logger.info("Umpires ingestion complete", extra={"processed": processed, "failed": len(failed_game_pks)})

    if failed_game_pks:
        logger.error("Failed game PKs", extra={"game_pks": failed_game_pks})
        raise SystemExit(1)


def _ingest_schedule(bucket: str, start_year: int, end_year: int) -> None:
    manifest = download_json_from_gcs(bucket, _SCHEDULE_MANIFEST) or {}
    completed_years = set(manifest.get("completed_years", []))

    for year in range(start_year, end_year + 1):
        if year in completed_years and year != date.today().year:
            logger.info("Skipping already-fetched year", extra={"year": year})
            continue
        games = fetch_schedule(date(year, 1, 1), date(year, 12, 31))
        upload_json_to_gcs(bucket, _schedule_path(year), games)
        completed_years.add(year)
        logger.info("Schedule ingestion complete", extra={"year": year, "games": len(games)})

    upload_json_to_gcs(bucket, _SCHEDULE_MANIFEST, {
        "completed_years": sorted(completed_years),
        "last_updated": date.today().isoformat(),
    })


def main() -> None:
    """Cloud Run Job entry point for MLB reference data backfill."""
    args = parse_args()
    bucket = args.bucket
    if not bucket:
        raise ValueError("GCS bucket must be provided via --bucket or GCS_BUCKET env var")

    if args.daily:
        yesterday = date.today() - timedelta(days=1)
        logger.info(f"Daily reference refresh: {yesterday}")
        games = fetch_schedule(yesterday, yesterday)
        failed_game_pks = []
        for game in games:
            game_pk = game["gamePk"]
            try:
                umpire = fetch_umpires_for_game(game_pk)
                if umpire:
                    game_date = date.fromisoformat(game["officialDate"])
                    existing = download_json_from_gcs(bucket, _umpire_path(game_date)) or []
                    existing.append(umpire)
                    upload_json_to_gcs(bucket, _umpire_path(game_date), existing)
            except Exception:
                logger.exception("Failed to ingest umpire data", extra={"game_pk": game_pk})
                failed_game_pks.append(game_pk)
        games_full = fetch_schedule(date(yesterday.year, 1, 1), date(yesterday.year, 12, 31))
        upload_json_to_gcs(bucket, _schedule_path(yesterday.year), games_full)
        if failed_game_pks:
            logger.error("Failed game PKs", extra={"game_pks": failed_game_pks})
            raise SystemExit(1)

    elif args.date:
        d = date.fromisoformat(args.date)
        logger.info(f"Single-date reference refresh: {d}")
        games = fetch_schedule(d, d)
        for game in games:
            umpire = fetch_umpires_for_game(game["gamePk"])
            if umpire:
                game_date = date.fromisoformat(game["officialDate"])
                existing = download_json_from_gcs(bucket, _umpire_path(game_date)) or []
                existing.append(umpire)
                upload_json_to_gcs(bucket, _umpire_path(game_date), existing)

    else:
        start_year = args.start_year
        end_year = args.end_year
        if end_year is None:
            raise ValueError("--end-year is required with --start-year")
        if start_year > end_year:
            raise ValueError("--start-year must be less than or equal to --end-year")

        logger.info(f"Starting reference backfill: {start_year}-{end_year}")
        _ingest_players(bucket)
        _ingest_schedule(bucket, start_year, end_year)
        _ingest_umpires(bucket, start_year, end_year)

    logger.info("Reference backfill process complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Reference backfill process crashed")
        raise
