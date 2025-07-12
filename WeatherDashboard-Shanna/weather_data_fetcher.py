
import requests                 
import time                    
import logging                 
from datetime import datetime
from typing import Dict, Optional  

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

        #Logger setup for error tracking
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

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
                    return response.json()          #Success — return parsed data
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

    def fetch_five_day_forecast(self, city, country=None, units='metric') -> Optional[Dict]:
        """
        Retrieves a 5-day forecast in 3-hour blocks.

        Args:
            city (str): City name.
            country (Optional[str]): 2-letter country code.
            units (str): Measurement system ('metric' by default).

        Returns:
            Optional[Dict]: Raw forecast data (to be grouped later in GUI).
        """
        location = f"{city},{country}" if country else city
        params = {"q": location, "units": units}
        return self._api_request("forecast", params)