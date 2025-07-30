import threading
import tkinter as tk
from tkinter import messagebox
from collections import defaultdict
from datetime import datetime, timedelta


class GetWeather:
      
    def __init__(self, fetcher, db, logger, root=None):
   
        self.fetcher = fetcher
        self.db = db
        self.logger = logger
        self.root = root
        self.current_weather_data = None
        
        # Callbacks for UI updates - components can register these
        self.ui_callbacks = {
            'on_weather_start': [],
            'on_weather_success': [],
            'on_weather_error': [],
            'on_forecast_success': []
        }
    
    def register_callback(self, event_type, callback):
        """Register a callback function for weather events"""
        if event_type in self.ui_callbacks:
            self.ui_callbacks[event_type].append(callback)
    
    def _trigger_callbacks(self, event_type, *args, **kwargs):
        """Trigger all callbacks for a specific event type"""
        for callback in self.ui_callbacks.get(event_type, []):
            try:
                if self.root:
                    self.root.after(0, lambda: callback(*args, **kwargs))
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error for {event_type}: {e}")
    
    def get_weather_threaded(self, city=None, country=None, units=None):
        """Start weather fetching in a separate thread"""
        threading.Thread(
            target=self.get_weather, 
            args=(city, country, units),
            daemon=True
        ).start()
    
    def get_weather(self, city=None, country=None, units=None):
                # Set defaults
        city = city or "Knoxville"
        country = country or "US"
        
        # Determine units based on country if not specified
        if units is None:
            units = "imperial" if country.upper() == "US" else "metric"
        
        try:
            # Trigger start callbacks
            self._trigger_callbacks('on_weather_start', city, country)
            
            # Fetch current weather
            current_weather = self.fetcher.fetch_current_weather(city, country, units)
            
            if current_weather:
                self.current_weather_data = current_weather
                
                # Store in database
                self.db.insert_reading(current_weather)
                
                # Trigger success callbacks
                self._trigger_callbacks('on_weather_success', current_weather, units)
                
                # Fetch forecast data
                self._fetch_forecast(city, country, units)
                
                return current_weather
            else:
                error_msg = "Could not fetch weather data"
                self._trigger_callbacks('on_weather_error', error_msg)
                return None
                
        except Exception as e:
            self.logger.error(f"Weather fetch error: {e}")
            error_msg = f"Weather fetch failed: {e}"
            self._trigger_callbacks('on_weather_error', error_msg)
            return None
    
    def _fetch_forecast(self, city, country, units):
        """Fetch and process forecast data"""
        try:
            forecast_data = self.fetcher.fetch_five_day_forecast(city, country, units)
            if forecast_data:
                daily_forecasts = self.extract_five_day_summary(forecast_data)
                self._trigger_callbacks('on_forecast_success', daily_forecasts, units)
                return daily_forecasts
        except Exception as e:
            self.logger.error(f"Forecast fetch error: {e}")
            return None
    
    def extract_five_day_summary(self, forecast):
    
        forecast_list = forecast.get("list", [])
        daily_data = defaultdict(list)

        # Organize forecast data by date
        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if dt_txt:
                date = dt_txt.split(" ")[0]
                daily_data[date].append(entry)

        five_day_forecasts = []

        # Get forecasts for 5 days
        for date in sorted(daily_data.keys())[:5]:
            entries = daily_data[date]
            # Prefer noon data, fallback to middle of day
            preferred_entry = next(
                (e for e in entries if "12:00:00" in e["dt_txt"]),
                entries[len(entries)//2]
            )
            five_day_forecasts.append(preferred_entry)

        return five_day_forecasts
    
    def get_current_weather_data(self):
        """Get the last fetched weather data"""
        return self.current_weather_data
    
    def refresh_weather(self, city=None, country=None, units=None):
        """Refresh weather data (alias for get_weather_threaded)"""
        self.get_weather_threaded(city, country, units)


# Example integration class showing how to use GetWeather
class WeatherComponent:
    """Example component showing GetWeather integration"""
    
    def __init__(self, parent, get_weather_instance, city_entry=None, country_entry=None):
        self.parent = parent
        self.get_weather = get_weather_instance
        self.city_entry = city_entry
        self.country_entry = country_entry
        
        # Register callbacks with GetWeather
        self.get_weather.register_callback('on_weather_start', self.on_weather_loading)
        self.get_weather.register_callback('on_weather_success', self.on_weather_updated)
        self.get_weather.register_callback('on_weather_error', self.on_weather_error)
        self.get_weather.register_callback('on_forecast_success', self.on_forecast_updated)
        
        # UI elements (these would be your actual UI components)
        self.temp_label = None
        self.city_label = None
        self.status_label = None
    
    def on_weather_loading(self, city, country):
        """Called when weather fetching starts"""
        if self.temp_label:
            self.temp_label.config(text="Loading...")
        if self.city_label:
            self.city_label.config(text=f"{city}, {country}")
        if self.status_label:
            self.status_label.config(text="Fetching weather data...")
    
    def on_weather_updated(self, weather_data, units):
        """Called when weather data is successfully fetched"""
        if self.temp_label:
            temp = weather_data.get("temperature", 0)
            temp_unit = "°F" if units == "imperial" else "°C"
            self.temp_label.config(text=f"{temp:.0f}{temp_unit}")
        
        if self.city_label:
            self.city_label.config(text=weather_data.get('city', 'Unknown'))
        
        if self.status_label:
            self.status_label.config(text="Weather updated successfully")
    
    def on_weather_error(self, error_message):
        """Called when weather fetching fails"""
        if self.status_label:
            self.status_label.config(text=f"Error: {error_message}")
        
        # Optionally show error dialog
        if self.parent:
            messagebox.showerror("Weather Error", error_message)
    
    def on_forecast_updated(self, forecast_data, units):
        """Called when forecast data is available"""
        # Handle forecast updates here
        if self.status_label:
            self.status_label.config(text=f"Forecast updated ({len(forecast_data)} days)")
    
    def request_weather_update(self):
        """Request a weather update using current city/country"""
        city = self.city_entry.get().strip() if self.city_entry else None
        country = self.country_entry.get().strip() if self.country_entry else None
        self.get_weather.get_weather_threaded(city, country)
        
   