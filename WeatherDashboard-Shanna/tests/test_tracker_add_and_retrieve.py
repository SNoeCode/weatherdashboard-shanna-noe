import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

import pytest
from automated_weather_tracker import AutomatedWeatherTracker
from weather_data_fetcher import WeatherDataFetcher
from weather_db import WeatherDB

def test_tracker_add_and_retrieve():
    api_key = os.getenv("WEATHER_API_KEY")
    assert api_key is not None, "❌ WEATHER_API_KEY not found in environment"

    # Instantiate system components
    db = WeatherDB()
    fetcher = WeatherDataFetcher(api_key)
    tracker = AutomatedWeatherTracker(collector=fetcher, database=db)

    # Add a test location
    test_city = "Miniapolis"
    test_country = "US"
    added = tracker.add_location(test_city, test_country)
    assert added, f"❌ Failed to add location {test_city}, {test_country}"

    # Retrieve active locations and confirm presence
    active = tracker.get_active_locations()
    assert any(loc["city"] == test_city and loc["country"] == test_country for loc in active), \
        f"❌ Location {test_city}, {test_country} not found in active list"

    print("✅ Tracker add/retrieve test passed")