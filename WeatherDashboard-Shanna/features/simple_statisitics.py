from collections import Counter
from typing import Dict

def get_weather_stats(db, city: str, country: str) -> Dict:
    """
    Analyzes recent weather readings for a city to extract simple statistics.

    Args:
        db: Your database interface with `fetch_recent()`.
        city (str): City name.
        country (str): 2-letter country code.

    Returns:
        Dict: A dictionary with min/max temperatures and the most common weather condition.
    """
    readings = db.fetch_recent(city, country, hours=48)
    if not readings:
        return {
            "min_temp": 0.0,
            "max_temp": 0.0,
            "common_conditions": "Unknown"
        }

    temps = [r["temp"] for r in readings if r.get("temp") is not None]
    summaries = [r["weather_summary"] for r in readings if r.get("weather_summary")]

    return {
        "min_temp": min(temps) if temps else 0.0,
        "max_temp": max(temps) if temps else 0.0,
        "common_conditions": Counter(summaries).most_common(1)[0][0] if summaries else "Unknown"
    }