import logging

from pandas import DataFrame
from pybaseball import statcast

logger = logging.getLogger(__name__)


def fetch_statcast_data(start_date: str, end_date: str) -> DataFrame:
    """Fetch Statcast data for the given date range."""
    try:
        data = statcast(start_date, end_date)
        return data
    except Exception as e:
        logger.error(f"Error fetching Statcast data: {e}")
        raise
