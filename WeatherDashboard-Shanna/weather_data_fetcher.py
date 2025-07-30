import sys
import requests                 
import time                    
import logging                 
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List,  Optional 
from config import Config
import os
class WeatherDataFetcher:
    def __init__(self, config: Config, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.config = config
        self.api_key = api_key or config.api_key
        self.base_url = base_url or config.base_url
        self.session = requests.Session()
        self.min_request_interval = 1.0
        self.last_request = 0
        self.failed_cities = {}
        self.logger = config.logger or logging.getLogger(__name__)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def register_failure(self, city: str):
            self.failed_cities[city] = self.failed_cities.get(city, 0) + 1

    def is_fake_or_unresolvable(self, city: str, threshold: int = 3) -> bool:
        city = city.lower()
        if city in {"testville", "demo city"}:
            return True
        return self.failed_cities.get(city.title(), 0) >= threshold


    def _delay_between_request(self):     
        elapsed_time = time.time() - self.last_request
        if elapsed_time < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed_time)
        self.last_request = time.time()

    def _api_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        self._delay_between_request() 

        url = f"{self.base_url}/{endpoint}"         
        params['appid'] = self.api_key              

        max_retries = 3                             
        retry_delays = [1, 2, 4]                

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)  #Send request

                if response.status_code == 200:
                    return response.json()   
                elif response.status_code != 200:
                    city = params.get("q", "Unknown").split(",")[0].title()
                    self.register_failure(city)
                    return None
                elif response.status_code == 401:
                    self.logger.error("❌ Invalid API key.")
                    return None
                elif response.status_code == 429:
                    self.logger.warning("⏳ Rate limited! Waiting 60 seconds...")
                    time.sleep(60)
                else:
                    self.logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
            except requests.RequestException as e:
                self.logger.warning(f"📡 Request error on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delays[attempt])  

        self.logger.error("🚫 Failed to get a valid response after retries")
        return None
      
    def fetch_current_weather(self, city: str, country: Optional[str] = None, units: str = 'metric') -> Optional[Dict]:
        city = city.strip().title()
        country = country.upper() if country else ""

        if self.is_fake_or_unresolvable(city):
            self.logger.warning(f"⛔️ Skipping persistently failing city: {city}")
            return None

        if country == "US":
            units = "imperial"
        else:
            units = "metric"

        location = f"{city},{country}" if country else city
        params = {"q": location, "units": units}

        raw_data = self._api_request("weather", params)
        if not raw_data:
            return None

        try:
            country_code = raw_data["sys"]["country"]
            temp = raw_data["main"]["temp"]
            feels_like = raw_data["main"]["feels_like"]

            temp_unit = "°F" if units == "imperial" else "°C"
            
            temp_display = round(temp, 1)
            feels_display = round(feels_like, 1)

            return {
                "timestamp": datetime.utcfromtimestamp(raw_data["dt"]).isoformat(),
                "api_timestamp": datetime.utcnow().isoformat(),
                "city": raw_data.get("name", city),
                "country": country_code,
                "temperature": temp_display,
                "condition": raw_data["weather"][0].get("description", "Unknown"),
                "temp": temp_display,
                "feels_like": feels_display,
                "temp_unit": temp_unit, 
                "humidity": raw_data["main"]["humidity"],
                "pressure": raw_data["main"]["pressure"],
                "weather_summary": raw_data["weather"][0]["main"],
                "weather_detail": raw_data["weather"][0].get("description", "Unknown"),
                "wind_speed": raw_data["wind"].get("speed"),
                "wind_direction": raw_data["wind"].get("deg"),
                "cloudiness": raw_data["clouds"].get("all"),
                "visibility": raw_data.get("visibility"),
                "units": units 
            }
        except (KeyError, IndexError, TypeError) as err:
            self.logger.error(f"🧨 Data parsing error for {location}: {err}")
            return None
   
        
    def fetch_five_day_forecast(self, city: str, country: Optional[str] = None, units: str = "metric") -> Optional[Dict]:
        location = f"{city},{country}" if country else city
        params = {"q": location, "units": units}

        forecast = self._api_request("forecast", params)
        if forecast:
            self.logger.info(f"✅ Forecast list length: {len(forecast.get('list', []))}")
        else:
            self.logger.warning(f"❌ No forecast returned for: {location}")
        return forecast
    
    def fetch_recent(self, city, country, hours=3):
        forecast = self.fetch_five_day_forecast(city, country)
        if not forecast:
            return None

        now = datetime.utcnow()
        window = timedelta(hours=hours)

        recent_entries = [
            entry for entry in forecast["list"]
            if abs(datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S") - now) <= window
        ]

        return recent_entries if recent_entries else None

    def fetch_hourly_weather(self, city: str, state: str, country: str) -> Optional[Dict]:
        endpoint = "weather/hourly"  # or your provider-specific endpoint
        params = {"q": f"{city},{state},{country}", "units": "imperial"}
        params['appid'] = "67e0f6de342521f8dfbd7a7c74423ca7"
        response = self._api_request(endpoint, params)
        
        if not response:
            return None

        try:
            return {
                "Current Time": datetime.now().strftime("%m-%d-%y %H:%M:%S"),
                "City": city,
                "State": state,
                "Country": country,
                "Temperature": response["temp"],
                "Feels Like": response["feels_like"],
                "Humidity": response["humidity"],
                "Precipitation": response.get("precip", 0),
                "Pressure": response["pressure"],
                "Wind Speed": response["wind_speed"],
                "Wind Direction": response["wind_deg"],
                "Visibility": response["visibility"],
                "Sunrise": response["sunrise"],
                "Sunset": response["sunset"]
            }
        except Exception as e:
            self.logger.error(f"Error parsing hourly weather: {e}")
            return None

    def fetch_historical_weather(self, city: str, state: str, country: str) -> List[Dict]:
        endpoint = "weather/historical"
        params = {"q": f"{city},{state},{country}", "units": "imperial"}
        params['appid'] = os.getenv("HIST_DATA_API_KEY")  # you'll plug this into .env

        response = self._api_request(endpoint, params)
        if not response or "history" not in response:
            return []

        readings = []
        for entry in response["history"]:
            readings.append({
                "Current Time": datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%S").strftime("%m-%d-%y %H:%M:%S"),
                "City": city,
                "State": state,
                "Country": country,
                "Temperature": entry["temp"],
                "Feels Like": entry["feels_like"],
                "Humidity": entry["humidity"],
                "Precipitation": entry.get("precip", 0),
                "Pressure": entry["pressure"],
                "Wind Speed": entry["wind_speed"],
                "Wind Direction": entry["wind_deg"],
                "Visibility": entry["visibility"],
                "Sunrise": entry["sunrise"],
                "Sunset": entry["sunset"]
            })
        return readings



    def extract_five_day_summary(self, forecast: Dict) -> List[Dict]:      
        forecast_list = forecast.get("list", [])
        daily_data = defaultdict(list)

        # Organize forecast data by date
        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if dt_txt:
                date = dt_txt.split(" ")[0]
                daily_data[date].append(entry)

        five_day_forecasts = []

        # Get forecasts for the next 5 
        for date in sorted(daily_data.keys())[:5]:
            entries = daily_data[date]      
            preferred_entry = next(
                (e for e in entries if "12:00:00" in e["dt_txt"]),
                entries[len(entries)//2]  # fallback to middle of the day
            )
            five_day_forecasts.append(preferred_entry)

        return five_day_forecasts
