import sys
import requests                 
import time                    
import logging                 
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional 
import os

class WeatherDataFetcher:
    def __init__(self, config, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.config = config
        self.api_key = api_key or config.api_key
        self.base_url = base_url or config.base_url
        self.session = requests.Session()
        self.min_request_interval = 1.0
        self.last_request = 0
        self.failed_cities = {}
        self.logger = config.logger or logging.getLogger(__name__)
        
        # Validate API key on initialization
        self._validate_api_key()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _validate_api_key(self):
        """Validate API key with a simple API call"""
        if not self.api_key:
            self.logger.error("❌ No API key provided. Check your .env file.")
            return False
            
        # Test API key with a simple call
        test_url = f"{self.base_url}/weather"
        test_params = {
            "q": "London,UK",
            "appid": self.api_key
        }
        
        try:
            response = self.session.get(test_url, params=test_params, timeout=10)
            if response.status_code == 401:
                self.logger.error("❌ Invalid API key. Please check your OpenWeatherMap API key.")
                self.logger.error("💡 Make sure your API key is activated (can take up to 2 hours)")
                return False
            elif response.status_code == 200:
                self.logger.info("✅ API key validated successfully")
                return True
            else:
                self.logger.warning(f"⚠️ API key test returned status code: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Failed to validate API key: {e}")
            return False

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

    def _api_request(self, endpoint: str, params: Dict, base_url: Optional[str] = None) -> Optional[Dict]:
        self._delay_between_request() 

        url = f"{base_url or self.base_url}/{endpoint}"         
        params['appid'] = self.api_key              

        max_retries = 3                             
        retry_delays = [1, 2, 4]                

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    return response.json()   
                elif response.status_code == 401:
                    self.logger.error("❌ Invalid API key. Please check your OpenWeatherMap API key.")
                    self.logger.error("💡 Tips:")
                    self.logger.error("   - Verify API key in your .env file")
                    self.logger.error("   - New API keys take up to 2 hours to activate")
                    self.logger.error("   - Make sure you're using the correct subscription plan")
                    return None
                elif response.status_code == 429:
                    self.logger.warning("⏳ Rate limited! Waiting 60 seconds...")
                    time.sleep(60)
                elif response.status_code == 404:
                    self.logger.warning(f"🌍 City not found: {params.get('q', 'Unknown location')}")
                    if "q" in params:
                        city = params.get("q", "Unknown").split(",")[0].title()
                        self.register_failure(city)
                    return None
                else:
                    self.logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                    if "q" in params:
                        city = params.get("q", "Unknown").split(",")[0].title()
                        self.register_failure(city)
            except requests.RequestException as e:
                self.logger.warning(f"📡 Request error on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delays[attempt])  

        self.logger.error("🚫 Failed to get a valid response after retries")
        return None

    def get_coordinates(self, city: str, country: str) -> Optional[tuple]:
        """Get latitude and longitude for a city using geocoding API"""
        geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": f"{city},{country}",
            "limit": 1,
            "appid": self.api_key
        }
        
        try:
            response = self.session.get(geocoding_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0]['lat'], data[0]['lon']
            elif response.status_code == 401:
                self.logger.error("❌ Invalid API key for geocoding")
                return None
        except Exception as e:
            self.logger.error(f"Error getting coordinates: {e}")
        return None

    def fetch_weather_alerts(self, city: str, country: Optional[str] = None) -> List[Dict]:
        """Fetch weather alerts for a location"""
        try:
            # Get coordinates first
            coords = self.get_coordinates(city, country or "")
            if not coords:
                return []
            
            lat, lon = coords
            
            # Use One Call API for alerts (requires coordinates)
            alerts_url = f"{self.base_url}/onecall"
            params = {
                "lat": lat,
                "lon": lon,
                "exclude": "minutely,daily",  # We only want alerts
                "appid": self.api_key
            }
            
            response = self.session.get(alerts_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('alerts', [])
            else:
                self.logger.warning(f"Could not fetch alerts: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching weather alerts: {e}")
            return []

    def fetch_current_weather(self, city: str, country: Optional[str] = None, units: str = 'metric') -> Optional[Dict]:
        """Fetch current weather with enhanced error handling and additional data"""
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
            temp_min = raw_data["main"].get("temp_min", temp)
            temp_max = raw_data["main"].get("temp_max", temp)

            temp_unit = "°F" if units == "imperial" else "°C"
            
            temp_display = round(temp, 1)
            feels_display = round(feels_like, 1)
            temp_min_display = round(temp_min, 1)
            temp_max_display = round(temp_max, 1)

            # Format sunrise and sunset times
            sunrise_timestamp = raw_data["sys"].get("sunrise")
            sunset_timestamp = raw_data["sys"].get("sunset")
            
            sunrise_time = ""
            sunset_time = ""
            if sunrise_timestamp:
                sunrise_dt = datetime.fromtimestamp(sunrise_timestamp)
                sunrise_time = sunrise_dt.strftime("%I:%M %p")
            if sunset_timestamp:
                sunset_dt = datetime.fromtimestamp(sunset_timestamp)
                sunset_time = sunset_dt.strftime("%I:%M %p")

            # Fetch weather alerts
            alerts = self.fetch_weather_alerts(city, country)

            return {
                "timestamp": datetime.utcfromtimestamp(raw_data["dt"]).isoformat(),
                "api_timestamp": datetime.utcnow().isoformat(),
                "city": raw_data.get("name", city),
                "country": country_code,
                "state": "",
                "temperature": temp_display,
                "condition": raw_data["weather"][0].get("description", "Unknown"),
                "temp": temp_display,
                "temp_min": temp_min_display,
                "temp_max": temp_max_display,
                "feels_like": feels_display,
                "temp_unit": temp_unit, 
                "humidity": raw_data["main"]["humidity"],
                "pressure": raw_data["main"]["pressure"],
                "weather_summary": raw_data["weather"][0]["main"],
                "weather_detail": raw_data["weather"][0].get("description", "Unknown"),
                "wind_speed": raw_data["wind"].get("speed", 0),
                "wind_direction": raw_data["wind"].get("deg", 0),
                "cloudiness": raw_data["clouds"].get("all", 0),
                "visibility": raw_data.get("visibility", 10000),
                "precipitation": 0,  # Basic API doesn't provide precipitation
                "sunrise": sunrise_time,
                "sunset": sunset_time,
                "alerts": alerts,  # Weather alerts
                "units": units 
            }
        except (KeyError, IndexError, TypeError) as err:
            self.logger.error(f"🧨 Data parsing error for {location}: {err}")
            return None

    def fetch_five_day_forecast(self, city: str, country: Optional[str] = None, units: str = "metric") -> Optional[Dict]:
        """Fetch 5-day forecast with enhanced error handling"""
        location = f"{city},{country}" if country else city
        params = {"q": location, "units": units}

        forecast = self._api_request("forecast", params)
        if forecast:
            self.logger.info(f"✅ Forecast list length: {len(forecast.get('list', []))}")
            
            # Enhance forecast data with daily highs and lows
            enhanced_forecast = self._enhance_forecast_data(forecast)
            return enhanced_forecast
        else:
            self.logger.warning(f"❌ No forecast returned for: {location}")
        return forecast

    def _enhance_forecast_data(self, forecast_data: Dict) -> Dict:
        """Enhance forecast data with better daily aggregation"""
        if not forecast_data or 'list' not in forecast_data:
            return forecast_data
        
        forecast_list = forecast_data.get("list", [])
        daily_data = defaultdict(list)

        # Organize forecast data by date
        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if dt_txt:
                date = dt_txt.split(" ")[0]
                daily_data[date].append(entry)

        # Calculate actual daily highs and lows
        enhanced_list = []
        for date in sorted(daily_data.keys())[:5]:
            entries = daily_data[date]
            
            # Calculate daily statistics
            temps = [entry["main"]["temp"] for entry in entries]
            feels_like_temps = [entry["main"]["feels_like"] for entry in entries]
            humidity_vals = [entry["main"]["humidity"] for entry in entries]
            
            daily_high = max(temps)
            daily_low = min(temps)
            avg_feels_like = sum(feels_like_temps) / len(feels_like_temps)
            avg_humidity = sum(humidity_vals) / len(humidity_vals)
            
            # Get representative weather condition (preferably midday)
            preferred_entry = next(
                (e for e in entries if "12:00:00" in e["dt_txt"]),
                entries[len(entries)//2]
            )
            
            # Create enhanced entry
            enhanced_entry = preferred_entry.copy()
            enhanced_entry["main"]["temp_max"] = daily_high
            enhanced_entry["main"]["temp_min"] = daily_low
            enhanced_entry["main"]["feels_like"] = avg_feels_like
            enhanced_entry["main"]["humidity"] = avg_humidity
            enhanced_entry["daily_stats"] = {
                "temp_max": daily_high,
                "temp_min": daily_low,
                "temp_range": daily_high - daily_low,
                "entries_count": len(entries)
            }
            
            enhanced_list.append(enhanced_entry)
        
        # Update the forecast data
        enhanced_forecast = forecast_data.copy()
        enhanced_forecast["list"] = enhanced_list
        enhanced_forecast["enhanced"] = True
        
        return enhanced_forecast

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

    def fetch_hourly_forecast(self, city: str, country: Optional[str] = None, units: str = 'metric') -> List[Dict]:
        """Fetch hourly forecast using basic 5-day forecast API"""
        location = f"{city},{country}" if country else city
        params = {"q": location, "units": units}
        
        forecast = self._api_request("forecast", params)
        if not forecast:
            return []
        
        try:
            hourly_data = []
            forecast_list = forecast.get("list", [])
            
            # Get next 8 entries (24 hours worth of 3-hour intervals)
            for entry in forecast_list[:8]:
                dt_timestamp = entry.get("dt")
                if dt_timestamp:
                    dt = datetime.utcfromtimestamp(dt_timestamp)
                    
                    hourly_entry = {
                        "datetime": dt,
                        "time": dt.strftime("%H:%M"),
                        "date": dt.strftime("%m/%d"),
                        "temp": entry["main"]["temp"],
                        "feels_like": entry["main"]["feels_like"],
                        "temp_min": entry["main"].get("temp_min", entry["main"]["temp"]),
                        "temp_max": entry["main"].get("temp_max", entry["main"]["temp"]),
                        "humidity": entry["main"]["humidity"],
                        "pressure": entry["main"]["pressure"],
                        "weather_main": entry["weather"][0]["main"],
                        "weather_desc": entry["weather"][0]["description"],
                        "wind_speed": entry["wind"].get("speed", 0),
                        "wind_deg": entry["wind"].get("deg", 0),
                        "clouds": entry["clouds"].get("all", 0),
                        "visibility": entry.get("visibility", 10000),
                        "pop": entry.get("pop", 0) * 100  # Probability of precipitation
                    }
                    hourly_data.append(hourly_entry)
            
            return hourly_data
            
        except Exception as e:
            self.logger.error(f"Error parsing hourly forecast: {e}")
            return []

    def extract_five_day_summary(self, forecast: Dict) -> List[Dict]:      
        """Extract 5-day summary with proper daily highs and lows"""
        if not forecast or 'list' not in forecast:
            return []
            
        forecast_list = forecast.get("list", [])
        daily_data = defaultdict(list)

        # Organize forecast data by date
        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if dt_txt:
                date = dt_txt.split(" ")[0]
                daily_data[date].append(entry)

        five_day_forecasts = []

        # Get forecasts for the next 5 days
        for date in sorted(daily_data.keys())[:5]:
            entries = daily_data[date]
            
            # Calculate actual daily high and low temperatures
            temps = [entry["main"]["temp"] for entry in entries]
            temp_max = max(temps) if temps else 0
            temp_min = min(temps) if temps else 0
            
            # Get representative weather conditions (prefer midday)
            preferred_entry = next(
                (e for e in entries if "12:00:00" in e["dt_txt"]),
                entries[len(entries)//2] if entries else None
            )
            
            if preferred_entry:
                # Create enhanced daily summary
                daily_summary = {
                    "date": date,
                    "dt_txt": preferred_entry["dt_txt"],
                    "dt": preferred_entry["dt"],
                    "main": {
                        "temp": preferred_entry["main"]["temp"],
                        "temp_min": temp_min,
                        "temp_max": temp_max,
                        "feels_like": preferred_entry["main"]["feels_like"],
                        "pressure": preferred_entry["main"]["pressure"],
                        "humidity": preferred_entry["main"]["humidity"]
                    },
                    "weather": preferred_entry["weather"],
                    "clouds": preferred_entry["clouds"],
                    "wind": preferred_entry["wind"],
                    "visibility": preferred_entry.get("visibility", 10000),
                    "pop": preferred_entry.get("pop", 0),
                    "daily_range": temp_max - temp_min,
                    "entries_count": len(entries)
                }
                five_day_forecasts.append(daily_summary)

        return five_day_forecasts

    def fetch_extended_forecast(self, city: str, country: Optional[str] = None, units: str = 'metric') -> Optional[Dict]:
        """Fetch extended forecast with better daily aggregation"""
        try:
            # Get coordinates for One Call API (if available)
            coords = self.get_coordinates(city, country or "")
            if coords:
                lat, lon = coords
                
                # Try One Call API for better daily forecasts
                onecall_url = f"{self.base_url}/onecall"
                params = {
                    "lat": lat,
                    "lon": lon,
                    "exclude": "minutely,alerts",
                    "units": units,
                    "appid": self.api_key
                }
                
                response = self.session.get(onecall_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data
                else:
                    self.logger.warning(f"One Call API failed: {response.status_code}")
            
            # Fallback to regular 5-day forecast
            return self.fetch_five_day_forecast(city, country, units)
            
        except Exception as e:
            self.logger.error(f"Error fetching extended forecast: {e}")
            return self.fetch_five_day_forecast(city, country, units)

    def fetch_weather_with_alerts(self, city: str, country: Optional[str] = None, units: str = 'metric') -> Optional[Dict]:
        """Fetch current weather with integrated alerts"""
        # Get basic weather data
        weather_data = self.fetch_current_weather(city, country, units)
        if not weather_data:
            return None
        
        # Try to get additional alerts if not already included
        if not weather_data.get('alerts'):
            try:
                alerts = self.fetch_weather_alerts(city, country)
                weather_data['alerts'] = alerts
            except Exception as e:
                self.logger.error(f"Error fetching alerts: {e}")
                weather_data['alerts'] = []
        
        return weather_data

    def fetch_sunrise_sunset_enhanced(self, city: str, country: Optional[str] = None) -> Dict:
        """Fetch enhanced sunrise/sunset information"""
        try:
            coords = self.get_coordinates(city, country or "")
            if not coords:
                return {}
            
            lat, lon = coords
            
            # Use a sunrise-sunset API for more detailed information
            # This is a backup method if you want more detailed sun information
            sunrise_api_url = f"https://api.sunrise-sunset.org/json"
            params = {
                "lat": lat,
                "lng": lon,
                "formatted": 0
            }
            
            response = self.session.get(sunrise_api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    results = data.get("results", {})
                    
                    # Parse and format times
                    sunrise_utc = results.get("sunrise")
                    sunset_utc = results.get("sunset")
                    
                    if sunrise_utc and sunset_utc:
                        sunrise_dt = datetime.fromisoformat(sunrise_utc.replace('Z', '+00:00'))
                        sunset_dt = datetime.fromisoformat(sunset_utc.replace('Z', '+00:00'))
                        
                        # Convert to local time (simplified - you might want to use proper timezone handling)
                        sunrise_local = sunrise_dt.strftime("%I:%M %p")
                        sunset_local = sunset_dt.strftime("%I:%M %p")
                        
                        return {
                            "sunrise": sunrise_local,
                            "sunset": sunset_local,
                            "day_length": results.get("day_length"),
                            "solar_noon": results.get("solar_noon"),
                            "civil_twilight_begin": results.get("civil_twilight_begin"),
                            "civil_twilight_end": results.get("civil_twilight_end")
                        }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error fetching sunrise/sunset: {e}")
            return {}

    def fetch_historical_weather(self, city: str, state: str, country: str) -> List[Dict]:
        """Fetch historical weather data"""
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

    def get_weather_icon_path(self, weather_main: str, weather_desc: str = "") -> str:
        """Get the path to weather icon based on condition"""
        # Map weather conditions to icon filenames
        icon_map = {
            "Clear": "sunny.png",
            "Clouds": "cloudy.png",
            "Rain": "rainy.png",
            "Drizzle": "drizzle.png",
            "Thunderstorm": "thunderstorm.png",
            "Snow": "snowy.png",
            "Mist": "misty.png",
            "Fog": "foggy.png",
            "Haze": "hazy.png"
        }
        
        # Default icon path (assumes icons are in an 'icons' folder)
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        icon_filename = icon_map.get(weather_main, "default.png")
        icon_path = os.path.join(icons_dir, icon_filename)
        
        # Check if icon file exists, otherwise return default
        if os.path.exists(icon_path):
            return icon_path
        else:
            # Return a default icon path or None
            default_path = os.path.join(icons_dir, "default.png")
            return default_path if os.path.exists(default_path) else None

    def format_weather_summary(self, weather_data: Dict) -> str:
        """Format weather data into a readable summary"""
        if not weather_data:
            return "No weather data available"
        
        city = weather_data.get('city', 'Unknown')
        temp = weather_data.get('temperature', 0)
        temp_unit = weather_data.get('temp_unit', '°C')
        condition = weather_data.get('weather_detail', 'Unknown')
        humidity = weather_data.get('humidity', 0)
        wind_speed = weather_data.get('wind_speed', 0)
        
        summary = f"Weather in {city}: {temp:.0f}{temp_unit}, {condition.title()}"
        summary += f"\nHumidity: {humidity}%, Wind: {wind_speed} m/s"
        
        # Add alerts if present
        alerts = weather_data.get('alerts', [])
        if alerts:
            summary += f"\n⚠️ {len(alerts)} weather alert(s) active"
        
        # Add sunrise/sunset if available
        sunrise = weather_data.get('sunrise')
        sunset = weather_data.get('sunset')
        if sunrise and sunset:
            summary += f"\n🌅 Sunrise: {sunrise}, 🌇 Sunset: {sunset}"
        
        return summary