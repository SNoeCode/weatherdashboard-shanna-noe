import os
import logging
from dotenv import load_dotenv
from weather_data_fetcher import WeatherDataFetcher
from weather_db import WeatherDB
from automated_weather_tracker import AutomatedWeatherTracker
from weather_display_ui import WeatherAppGUI
from config import Config
import threading


load_dotenv()

if __name__ == "__main__":
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise ValueError("WEATHER_API_KEY not set in .env")

    config = Config.load_from_env()

    db = WeatherDB()
    db.update_location("Salt Lake City", "US", latitude=40.7608, longitude=-111.8910, timezone="America/Denver")
    db.update_location("Knoxville", "US", latitude=35.9606, longitude=-83.9207, timezone="America/New_York")
    db.update_location("Tokyo", "JP", latitude=35.6828, longitude=139.7595, timezone="Asia/Tokyo")
    db.export_locations_to_csv()

    print("\n🔍 Recent Weather Errors:")
    errors = db.get_error_log(limit=10)
    for err in errors:
        print(f"- {err['timestamp']} | {err['city']}, {err['country']} | {err['status']} → {err.get('error', 'N/A')}")

    fetcher = WeatherDataFetcher(api_key=config.api_key, base_url=config.base_url)
    # fetcher = WeatherDataFetcher(api_key)
    tracker = AutomatedWeatherTracker(collector=fetcher, database=db)

    tracker.add_location("Salt Lake City", "US")
    tracker.add_location("Knoxville", "US")
    tracker.add_location("Tokyo", "JP")



    # tracker.start_scheduled_collection(interval_minutes=30)
    threading.Thread(target=tracker.start_scheduled_collection, args=(30,), daemon=True).start()
    tracker.collect_all_locations()
    city = "Knoxville"
    country = "US"
    forecast_data = fetcher.fetch_five_day_forecast(city, country)

    if forecast_data:
        five_day_summary = fetcher.extract_five_day_summary(forecast_data)
        print(f"\n📅 5-Day Forecast for {city}, {country}:")
        for entry in five_day_summary:
            dt_txt = entry["dt_txt"]
            temp = entry["main"]["temp"]
            description = entry["weather"][0]["description"]
            print(f"{dt_txt} | {temp:.1f}°C | {description}")
    else:
        print("❌ Could not fetch forecast data.")

    print("✅ Launching Weather Dashboard GUI...")
    config = Config.load_from_env()
    logger = logging.getLogger("WeatherDashboard")
    app = WeatherAppGUI(fetcher=fetcher, db=db, tracker=tracker, logger=logger)
    print("✅ Launching Weather Dashboard GUI...")
    try:
        app.run()
    except Exception as e:
        print(f"❌ GUI failed to launch: {e}")

