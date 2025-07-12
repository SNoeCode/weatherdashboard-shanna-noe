import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Load .env file

def test_weather_api_connection():
    api_key = os.getenv("WEATHER_API_KEY")
    assert api_key, "❌ API key not found in environment"

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": "Knoxville,US",
        "appid": api_key,
    }

    response = requests.get(url, params=params)
    assert response.status_code == 200, f"❌ Response status: {response.status_code}"
    data = response.json()
    assert "weather" in data and "main" in data, "❌ Missing expected fields"

    print("✅ API connectivity and structure OK")

