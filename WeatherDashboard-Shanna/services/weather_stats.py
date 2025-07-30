from datetime import datetime
import csv
import logging
from typing import Dict, Optional
from config import Config

def get_weather_stats(db, city: str, state: str, country: str, days: int = 30) -> Dict:
    logger = logging.getLogger(__name__)
    hours = days * 24
    readings = db.fetch_recent(city, country, hours)

    if not readings:
        stats = {
            "avg_temp": "N/A", "min_temp": "N/A", "max_temp": "N/A",
            "humidity_avg": "N/A", "pressure_avg": "N/A", "wind_avg": "N/A",
            "total_readings": 0, "period_days": days,
            "temp_unit": "°F" if country.upper() == "US" else "°C",
            "coverage_percentage": 0, "data_quality": "Missing"
        }
    else:
        temps = [r.get("temp", 0.0) for r in readings]
        humidities = [r.get("humidity", 0.0) for r in readings]
        pressures = [r.get("pressure", 0.0) for r in readings]
        winds = [r.get("wind_speed", 0.0) for r in readings]

        stats = {
            "avg_temp": round(sum(temps) / len(temps), 1),
            "min_temp": round(min(temps), 1),
            "max_temp": round(max(temps), 1),
            "humidity_avg": round(sum(humidities) / len(humidities), 1),
            "pressure_avg": round(sum(pressures) / len(pressures), 1),
            "wind_avg": round(sum(winds) / len(winds), 1) if winds else "N/A",
            "total_readings": len(readings),
            "period_days": days,
            "temp_unit": "°F" if country.upper() == "US" else "°C",
            "coverage_percentage": 100.0,
            "data_quality": "Raw"
        }

    row = format_weather_row(stats, city, state, country)
    save_to_csv(row)
    save_to_database(db, row)

    logger.info(f"✅ Raw stats for {city}, {country}: {stats}")
    return stats

def format_weather_row(stats: dict, city: str, state: str, country: str) -> dict:
    now = datetime.now().strftime("%m-%d-%y %H:%M:%S")
    return {
        "Timestamp": now,
        "City": city,
        "State": state,
        "Country": country,
        "Temperature": stats.get("avg_temp", "N/A"),
        "Feels Like": stats.get("avg_temp", "N/A"),
        "Humidity": stats.get("humidity_avg", "N/A"),
        "Precipitation": "N/A",
        "Pressure": stats.get("pressure_avg", "N/A"),
        "Wind Speed": stats.get("wind_avg", "N/A"),
        "Wind Direction": "N/A",
        "Visibility": "N/A",
        "Sunrise": "N/A",
        "Sunset": "N/A"
    }

def save_to_csv(row_data: dict, filename="weather_log.csv"):
    fieldnames = list(row_data.keys())
    try:
        with open(filename, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(row_data)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error writing to CSV: {e}")

def save_to_database(db, row_data: dict):
    try:
        db.save_weather_entry(row_data)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error writing to DB: {e}")