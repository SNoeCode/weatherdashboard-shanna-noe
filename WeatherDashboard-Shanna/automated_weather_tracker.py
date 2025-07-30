import schedule
import threading
import time
from typing import Dict, List
from weather_data_fetcher import WeatherDataFetcher
from weather_db import WeatherDB
from datetime import datetime
from weather_data_fetcher import WeatherDataFetcher

class AutomatedWeatherTracker:
    def __init__(self, collector: WeatherDataFetcher, database: WeatherDB):
        self.collector = collector
        self.database = database
        self.is_running = False
        self.collection_thread = None

    def add_location(self, city: str, country: str) -> bool:
        try:
            with self.database.get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO locations (city, country, is_active)
                    VALUES (?, ?, 1)
                """, (city, country))
            return True
        except Exception as e:
            print(f"[Add Location Error] {e}")
            return False

    def get_active_locations(self) -> List[Dict]:
        with self.database.get_connection() as conn:
            cursor = conn.execute("SELECT id, city, country FROM locations WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def collect_for_location(self, location: Dict):
        try:
            data = self.collector.fetch_current_weather(location["city"], location["country"])
            print(f"[FETCHED] {location['city']}: {data}")  # Debug print

            if data:
                success = self.database.insert_reading(data)
                status = "success" if success else "insert_failed"
                self.database.log_request("auto_fetch", location["id"], status)
            else:
                self.database.log_request("auto_fetch", location["id"], "api_error", "No data returned")
        except Exception as e:
            self.database.log_request("auto_fetch", location["id"], "error", str(e))

    def collect_all_locations(self):
        for loc in self.get_active_locations():
            self.collect_for_location(loc)
            time.sleep(1)

    def start_scheduled_collection(self, interval_minutes: int = 30):
        schedule.every(interval_minutes).minutes.do(self.collect_all_locations)
        schedule.run_all()

        def loop():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)

        self.is_running = True
        self.collection_thread = threading.Thread(target=loop, daemon=True)
        self.collection_thread.start()
        print(f"⏰ Automated weather tracking started — every {interval_minutes} min")

    def stop_collection(self):
        self.is_running = False
        schedule.clear()
        if self.collection_thread:
            self.collection_thread.join()
            self.collection_thread = None
        print("🛑 Tracking stopped.")

