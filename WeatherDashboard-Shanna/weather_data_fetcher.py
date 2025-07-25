
import requests                 
import time                    
import logging                 
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List,  Optional 


class WeatherDataFetcher:
    def __init__(self, api_key: str, base_url: str = "https://api.openweathermap.org/data/2.5"):
        """
        Initializes the WeatherDataFetcher with API key and setup.

        Args:
            api_key (str): Your OpenWeatherMap API key.
            base_url (str): Base URL for API requests.
        """
        self.api_key = api_key                      #API authentication
        self.base_url = base_url                    #Base URL for endpoint paths
        self.session = requests.Session()           #Reusable session for performance
        self.min_request_interval = 1.0             #Prevents over-requesting (rate limiting)
        self.last_request = 0                       #Tracks time of last call
        self.failed_cities = {}


        #Logger setup for error tracking
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
        """
        Enforces a minimum wait time between API requests.
        Prevents spamming the server and handles basic throttling.
        """
        elapsed_time = time.time() - self.last_request
        if elapsed_time < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed_time)
        self.last_request = time.time()

    def _api_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Performs a GET request to the specified API endpoint with retry logic.

        Args:
            endpoint (str): API route (e.g., "weather", "forecast").
            params (Dict): Query parameters including location and units.

        Returns:
            Optional[Dict]: Parsed JSON data or None if request fails.
        """
        self._delay_between_request()  #Apply delay before calling

        url = f"{self.base_url}/{endpoint}"         #Build full URL
        params['appid'] = self.api_key              #Attach API key

        max_retries = 3                             #Retry attempts
        retry_delays = [1, 2, 4]                     #Progressive backoff delays

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
                time.sleep(retry_delays[attempt])  #Wait before retrying

        self.logger.error("🚫 Failed to get a valid response after retries")
        return None

    def fetch_current_weather(self, city: str, country: Optional[str] = None, units: str = 'metric') -> Optional[Dict]:
        """
        Retrieves real-time weather data for a specified city.

        Args:
            city (str): City name.
            country (Optional[str]): Optional 2-letter country code.
            units (str): 'metric' (default), 'imperial', or 'standard'.

        Returns:
            Optional[Dict]: A structured weather data dictionary.
        """
        city = city.strip().title()
        if country:
            country = country.upper()
        else:
            country = ""



        if self.is_fake_or_unresolvable(city):
            self.logger.warning(f"⛔️ Skipping persistently failing city: {city}")
            return None




        location = f"{city},{country}" if country else city
        params = {"q": location, "units": units}

        raw_data = self._api_request("weather", params)
        if not raw_data:
            return None

        try:
            return {
                "timestamp": datetime.utcfromtimestamp(raw_data["dt"]).isoformat(),      #API timestamp
                "api_timestamp": datetime.utcnow().isoformat(),                          #Local timestamp
                "city": raw_data.get("name"),
                "country": raw_data["sys"]["country"],
                "temp": raw_data["main"]["temp"],
                "feels_like": raw_data["main"]["feels_like"],
                "humidity": raw_data["main"]["humidity"],
                "pressure": raw_data["main"]["pressure"],
                "weather_summary": raw_data["weather"][0]["main"],                      
                "weather_detail": raw_data["weather"][0].get("description", "Unknown"),
                "wind_speed": raw_data["wind"].get("speed"),
                "wind_direction": raw_data["wind"].get("deg"),
                "cloudiness": raw_data["clouds"].get("all"),
                "visibility": raw_data.get("visibility")
            }
        except (KeyError, IndexError, TypeError) as err:
            self.logger.error(f"🧨 Data parsing error for {location}: {err}")
            return None
        
        
    def fetch_five_day_forecast(self, city: str, country: Optional[str] = None, units: str = "metric") -> Optional[Dict]:
        """
        Retrieves a 5-day forecast in 3-hour intervals using city and country.
        """
        location = f"{city},{country}" if country else city
        params = {"q": location, "units": units}

        forecast = self._api_request("forecast", params)
        if forecast:
            self.logger.info(f"✅ Forecast list length: {len(forecast.get('list', []))}")
        else:
            self.logger.warning(f"❌ No forecast returned for: {location}")
        return forecast
    



    def extract_five_day_summary(self, forecast: Dict) -> List[Dict]:
        """
        Extracts 5 daily forecast summaries from 3-hour interval forecast data.
        Prefers 12:00 PM data point for each day if available.
        """
        forecast_list = forecast.get("list", [])
        daily_data = defaultdict(list)

        # Organize forecast data by date
        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if dt_txt:
                date = dt_txt.split(" ")[0]
                daily_data[date].append(entry)

        five_day_forecasts = []

        # Get forecasts for the next 5 distinct days
        for date in sorted(daily_data.keys())[:5]:
            entries = daily_data[date]
            # Prefer forecast at 12:00:00
            preferred_entry = next(
                (e for e in entries if "12:00:00" in e["dt_txt"]),
                entries[len(entries)//2]  # fallback to middle of the day
            )
            five_day_forecasts.append(preferred_entry)

        return five_day_forecasts
