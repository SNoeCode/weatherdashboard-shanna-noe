# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from datetime import datetime, timezone
# from weather_db import WeatherDB

# def test_insert_and_fetch_reading():
#     db = WeatherDB()
#     now = datetime.now(timezone.utc).isoformat()

#     sample = {
#         "timestamp": now,
#         "city": "Testville",
#         "country": "US",
#         "temp": 295.0,
#         "feels_like": 294.0,
#         "humidity": 50,
#         "pressure": 1013,
#         "weather_summary": "Clouds",
#         "weather_detail": "overcast clouds",
#         "wind_speed": 3.2,
#         "wind_direction": 100,
#         "cloudiness": 90,
#         "visibility": 10000,
#         "api_timestamp": now
#     }

#     assert db.insert_reading(sample), "❌ Failed to insert test reading"

#     recent = db.fetch_recent("Testville", "US", hours=1)
#     assert recent, "❌ No recent readings returned"
#     assert recent[0]["city"] == "Testville", "❌ Inserted city mismatch"

#     print("✅ Insert and fetch test passed")