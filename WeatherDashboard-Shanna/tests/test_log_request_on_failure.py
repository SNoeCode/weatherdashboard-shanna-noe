def test_log_request_on_failure():
    from weather_db import WeatherDB

    db = WeatherDB()

    # Step 1: Ensure test location exists
    city, country = "Testville", "US"
    with db.get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO locations (city, country) VALUES (?, ?)", (city, country))
        loc_id = conn.execute("SELECT id FROM locations WHERE city = ? AND country = ?", (city, country)).fetchone()["id"]

    # Step 2: Log error with valid location ID
    db.log_request(url="http://example.com", location_id=loc_id, status="error", error="404 not found")

    # Step 3: Assert that error is visible in joined logs
    recent_errors = db.get_error_log(limit=5)
    assert any("404 not found" in err.get("error", "") for err in recent_errors), "❌ Error log not recorded"

    print("✅ Log request error test passed")

