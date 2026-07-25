import logging
from datetime import date

import requests
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

_BASE_URL = "https://statsapi.mlb.com/api/v1"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30), before_sleep=before_sleep_log(logger, logging.WARNING))
def fetch_all_players() -> list[dict]:
    """Fetch all historical and active players from the MLB Stats API."""
    try:
        logger.info("Fetching all players")
        response = requests.get(f"{_BASE_URL}/sports/1/players", params={"season": "all"}, timeout=30)
        response.raise_for_status()
        players = response.json().get("people", [])
        logger.info("Fetched players", extra={"count": len(players)})
        return players
    except Exception:
        logger.exception("Failed to fetch players")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30), before_sleep=before_sleep_log(logger, logging.WARNING))
def fetch_schedule(start_date: date, end_date: date) -> list[dict]:
    """Fetch MLB schedule for all teams for the given date range."""
    try:
        logger.info("Fetching schedule", extra={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()})
        response = requests.get(
            f"{_BASE_URL}/schedule",
            params={
                "sportId": 1,
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "gameType": "R,P,F,D,L,W,C,S",
            },
            timeout=30,
        )
        response.raise_for_status()
        dates = response.json().get("dates", [])
        games = [game for d in dates for game in d.get("games", [])]
        logger.info("Fetched schedule", extra={"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "games": len(games)})
        return games
    except Exception:
        logger.exception("Failed to fetch schedule", extra={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()})
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30), before_sleep=before_sleep_log(logger, logging.WARNING))
def fetch_umpires_for_game(game_pk: int) -> dict | None:
    """Fetch home plate umpire for a given game from the boxscore."""
    try:
        response = requests.get(f"{_BASE_URL}/game/{game_pk}/boxscore", timeout=30)
        response.raise_for_status()
        officials = response.json().get("officials", [])
        for official in officials:
            if official.get("officialType") == "Home Plate":
                return {
                    "game_pk": game_pk,
                    "umpire_id": official["official"]["id"],
                    "umpire_name": official["official"]["fullName"],
                }
        return None
    except Exception:
        logger.exception("Failed to fetch umpires", extra={"game_pk": game_pk})
        raise
