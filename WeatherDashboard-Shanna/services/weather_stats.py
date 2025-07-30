from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

def get_weather_stats(db, city: str, country: str, days: int = 30) -> Dict:
    logger = logging.getLogger(__name__)
    hours = days * 24
    readings = db.fetch_recent(city, country, hours)

    cleaned = []
    for r in readings:
        try:
            if not isinstance(r, dict):
                continue

            temp_c = r.get("temp")
            humidity = r.get("humidity")
            pressure = r.get("pressure")
            wind = r.get("wind_speed", 0.0)  # default to 0 if missing

            # Convert Celsius to Fahrenheit if in US
            temp_f = (temp_c) if country.upper() == "US" else temp_c

            if (
                isinstance(temp_f, (int, float)) and 50 <= temp_f <= 130 and
                isinstance(humidity, (int, float)) and 0 <= humidity <= 100 and
                isinstance(pressure, (int, float)) and 900 <= pressure <= 1100 and
                isinstance(wind, (int, float)) and 0 <= wind <= 150
            ):
                cleaned.append({
                    "temp": round(temp_f, 2),
                    "humidity": humidity,
                    "pressure": pressure,
                    "wind_speed": wind
                })
            else:
                logger.warning(f"[Cleaner] Skipped invalid reading: {r}")
        except Exception as e:
            logger.warning(f"[Cleaner] Error cleaning reading {r}: {e}")

    if not cleaned:
        return {
            "avg_temp": "N/A", "min_temp": "N/A", "max_temp": "N/A",
            "humidity_avg": "N/A", "pressure_avg": "N/A", "wind_avg": "N/A",
            "total_readings": 0, "period_days": days,
            "temp_unit": "°F" if country.upper() == "US" else "°C",
            "coverage_percentage": 0, "data_quality": "Poor"
        }

    temps = [r["temp"] for r in cleaned]
    humidities = [r["humidity"] for r in cleaned]
    pressures = [r["pressure"] for r in cleaned]
    winds = [r["wind_speed"] for r in cleaned]

    stats = {
        "avg_temp": round(sum(temps) / len(temps), 1),
        "min_temp": round(min(temps), 1),
        "max_temp": round(max(temps), 1),
        "humidity_avg": round(sum(humidities) / len(humidities), 1),
        "pressure_avg": round(sum(pressures) / len(pressures), 1),
        "wind_avg": round(sum(winds) / len(winds), 1) if winds else "N/A",
        "total_readings": len(cleaned),
        "period_days": days,
        "temp_unit": "°F" if country.upper() == "US" else "°C",
        "coverage_percentage": round(len(cleaned) / len(readings) * 100, 1),
        "data_quality": "Good" if len(cleaned) > 20 else "Fair"
    }

    logger.info(f"✅ Clean stats for {city}, {country}: {stats}")
    return stats