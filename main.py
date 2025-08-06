import os
import logging
from dotenv import load_dotenv
from weather_data_fetcher import WeatherDataFetcher
from weather_db import WeatherDB
from automated_weather_tracker import AutomatedWeatherTracker
from weather_display_ui import WeatherAppGUI
from config import Config
import threading
import os
import logging
import threading


load_dotenv()

def initialize_system():
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise ValueError("WEATHER_API_KEY not set in .env")

    config = Config.load_from_env()
    fetcher = WeatherDataFetcher(config)
    db = WeatherDB(fetcher)

    # Add predefined locations
    locations = [
        ("Salt Lake City", "US", 40.7608, -111.8910, "America/Denver"),
        ("Knoxville", "US", 35.9606, -83.9207, "America/New_York"),
        ("Tokyo", "JP", 35.6828, 139.7595, "Asia/Tokyo"),
    ]

    for city, country, lat, lon, tz in locations:
        db.update_location(city, country, latitude=lat, longitude=lon, timezone=tz)

    db.export_readings_to_csv("./data/weather_readings.csv")

    # Show error log preview
    print("\n🔍 Recent Weather Errors:")
    for err in db.get_error_log(limit=10):
        print(f"- {err['timestamp']} | {err['city']}, {err['country']} | {err['status']} → {err.get('error', 'N/A')}")

    return config, fetcher, db

def run_dashboard(config, fetcher, db):
    tracker = AutomatedWeatherTracker(collector=fetcher, database=db)
    
    for city in db.get_all_locations():
        tracker.add_location(city["city"], city["country"])

    threading.Thread(target=tracker.start_scheduled_collection, args=(30,), daemon=True).start()
    tracker.collect_all_locations()
    db.export_readings_to_csv("weather_readings.csv")
    # Show forecast preview for Knoxville
    city, country = "Knoxville", "US"
    forecast_data = fetcher.fetch_five_day_forecast(city, country)
   
    if forecast_data:
        five_day_summary = fetcher.extract_five_day_summary(forecast_data)
        print(f"\n📅 5-Day Forecast for {city}, {country}:")
        for entry in five_day_summary:
            print(f"{entry['dt_txt']} | {entry['main']['temp']:.1f}°C | {entry['weather'][0]['description']}")
    else:
        print("❌ Could not fetch forecast data.")

    # Launch GUI
    print("✅ Launching Weather Dashboard GUI...")
    logger = logging.getLogger("WeatherDashboard")
    app = WeatherAppGUI(fetcher=fetcher, db=db, tracker=tracker, logger=logger, cfg=config)

    try:
        app.run()
    except Exception as e:
        print(f"❌ GUI failed to launch: {e}")

if __name__ == "__main__":
    config, fetcher, db = initialize_system()
    run_dashboard(config, fetcher, db)