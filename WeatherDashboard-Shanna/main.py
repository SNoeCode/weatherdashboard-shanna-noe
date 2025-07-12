from pathlib import Path
import os
import tkinter as tk
from tkinter import ttk, messagebox
from dotenv import load_dotenv
from weather_data_fetcher import WeatherDataFetcher
from weather_db import WeatherDB
from automated_weather_tracker import AutomatedWeatherTracker
from weather_display_ui import WeatherAppGUI  
from config import Config


load_dotenv()

if __name__ == "__main__":
    #Initialize system components
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise ValueError("WEATHER_API_KEY not set in .env")
    
    config = Config.load_from_env()



    db = WeatherDB()
    db.update_location("Salt Lake City", "US", latitude=40.7608, longitude=-111.8910, timezone="America/Denver")
    db.update_location("Knoxville", "US", latitude=35.9606, longitude=-83.9207, timezone="America/New_York")
    db.update_location("Tokyo", "JP", latitude=35.6828, longitude=139.7595, timezone="Asia/Tokyo")    


    db.export_locations_to_csv()
    #Show recent API errors before app starts
    print("\n🔍 Recent Weather Errors:")
    errors = db.get_error_log(limit=10)
    for err in errors:
        print(f"- {err['timestamp']} | {err['city']}, {err['country']} | {err['status']} → {err.get('error', 'N/A')}")
    fetcher = WeatherDataFetcher(api_key)
    tracker = AutomatedWeatherTracker(collector=fetcher, database=db)

    #Add default cities for tracking
    tracker.add_location("Salt Lake City", "US")
    tracker.add_location("Knoxville", "US")
    tracker.add_location("Tokyo", "JP")
    tracker.start_scheduled_collection(interval_minutes=30)
    tracker.collect_all_locations() 


    
    import logging
    logger = logging.getLogger("WeatherDashboard")
    app = WeatherAppGUI(fetcher=fetcher, db=db, tracker=tracker, logger=logger)
    app.run()