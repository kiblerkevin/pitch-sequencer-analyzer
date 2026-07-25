import logging

from pandas import DataFrame
from pybaseball import statcast
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30), before_sleep=before_sleep_log(logger, logging.WARNING))
def fetch_statcast_data(start_date: str, end_date: str) -> DataFrame:
    """Fetch Statcast data for the given date range."""
    try:
        logger.info(
            "Fetching Statcast data",
            extra={"start_date": start_date, "end_date": end_date},
        )
        data = statcast(start_date, end_date)
        logger.info(
            "Statcast fetch completed",
            extra={"start_date": start_date, "end_date": end_date, "rows": len(data) if data is not None else None},
        )
        return data
    except Exception:
        logger.exception(
            "Statcast fetch failed",
            extra={"start_date": start_date, "end_date": end_date},
        )
        raise
