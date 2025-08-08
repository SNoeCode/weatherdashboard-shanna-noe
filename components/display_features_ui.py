from typing import Dict, Optional, Union
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter, HourLocator
import tkinter as tk
from PIL import Image, ImageTk
import pandas as pd
from matplotlib.dates import DateFormatter, HourLocator
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import cast, Optional
from features.weather_icons import WeatherIconManager
from utils.date_time_utils import format_local_time
from utils.emoji import WeatherEmoji

class DisplayFeatures:
    def __init__(self, parent, theme_manager, db, logger, fetcher, cfg, city_entry=None, country_entry=None):
        self.parent = parent
        self.theme_manager = theme_manager
        self.db = db
        self.logger = logger
        self.fetcher = fetcher
        self.cfg = cfg 
        
        # Initialize UI element references 
        self.city_entry = city_entry
        self.country_entry = country_entry
        self.stats_label = None
        self.temp_label = None
        self.city_label = None
        self.desc_label = None
        self.icon_label = None
        self.summary_label = None
        self.details_frame = None
        self.forecast_items_frame = None
        self.current_weather_data = None  # Store current weather data
               
        self.widgets: Dict[str, Optional[Union[tk.Widget, tk.Frame, tk.Label]]] = {
            'temp_label': None,
            'city_label': None,
            'desc_label': None,
            'icon_label': None,
            'details_frame': None,
            'forecast_items_frame': None,
            'hourly_scroll_frame': None,
            'graph_container': None,
            'activity_content_frame': None
        }
    
    def set_ui_references(self, **kwargs):
        """Set references to UI elements"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            if key in self.widgets:
                self.widgets[key] = value
    
    def get_icon_path(self, weather_main):
        """Get icon path for weather condition"""
        try:
            icon_mgr = WeatherIconManager()
            return icon_mgr.get_icon_path(weather_main)
        except Exception as e:
            self.logger.warning(f"Could not get icon path: {e}")
            return None
    
    def display_current_weather(self, weather_data, units=None):
        """Display current weather data - SINGLE METHOD"""
        try:
            # Store the current weather data for other components to use
            self.current_weather_data = weather_data
            
            temp = weather_data.get("temperature", 0)
            temp_unit = weather_data.get("temp_unit")
            if not temp_unit:
                country = self.country_entry.get().strip() if self.country_entry else "US"
                temp_unit = "°F" if country.upper() == "US" else "°C"

            # Display temperature - make sure temp_label exists
            if self.temp_label:
                self.temp_label.config(text=f"{temp:.0f}{temp_unit}")
            
            # Display city and description
            if self.city_label:
                self.city_label.config(text=f"{weather_data.get('city', 'Unknown')}")
            
            if self.desc_label:
                self.desc_label.config(text=weather_data.get('weather_detail', '').title())

            # Update summary if summary_label exists
            if self.summary_label:
                humidity = weather_data.get("humidity", "N/A")
                wind_speed = weather_data.get("wind_speed", "N/A")
                summary = (
                    f"It's currently {temp:.0f}{temp_unit} in {weather_data.get('city', 'your area')}, "
                    f"with {weather_data.get('weather_detail', '').lower()} conditions. "
                    f"Humidity: {humidity}%, Wind Speed: {wind_speed} km/h."
                )
                self.summary_label.config(text=summary)

            # Update weather icon
            if self.icon_label:
                weather_main = weather_data.get("weather_summary", "Clear")
                icon_path = self.get_icon_path(weather_main)
                
                try:
                    if icon_path:
                        img = Image.open(icon_path).resize((80, 80))
                        photo = ImageTk.PhotoImage(img)
                        self.icon_label.config(image=photo, text="")
                        self.icon_label.image = photo
                    else:
                        raise Exception("No icon path available")
                except Exception as e:
                    # Fallback to emoji
                    emoji = WeatherEmoji.get_weather_emoji(weather_main)
                    self.icon_label.config(text=emoji, image="")
            
            # Update weather details
            if self.details_frame:
                self.update_weather_details(weather_data)
            
            self.logger.info(f"Weather display updated for {weather_data.get('city', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error displaying weather: {e}")

    def refresh_for_location(self, city, country):
        """Refresh all display components for a new location"""
        try:
            self.logger.info(f"Refreshing display features for {city}, {country}")
            
            # Update temperature graph
            self.update_temperature_graph(city, country)
            
            # Update hourly forecast  
            units = "imperial" if country.upper() == "US" else "metric"
            self.update_hourly_forecast(city, country, units)
            
        except Exception as e:
            self.logger.error(f"Error refreshing display for {city}, {country}: {e}")

    def update_weather_details(self, weather_data):
        """Update weather details section"""
        try:
            # Clear existing details
            if self.details_frame:
                for widget in self.details_frame.winfo_children():
                    widget.destroy()
            elif self.widgets['details_frame']:
                for widget in self.widgets['details_frame'].winfo_children():
                    widget.destroy()
            else:
                return  # No details frame available
            
            details = []
            # Determine temperature unit
            country = self.country_entry.get().strip() if self.country_entry else "US"
            temp_unit = "°F" if country.upper() == "US" else "°C"
            
            if 'feels_like' in weather_data:
                feels_like = weather_data['feels_like']
                details.append(f"Feels like: {feels_like:.0f}{temp_unit}")
            
            if 'humidity' in weather_data:
                details.append(f"Humidity: {weather_data['humidity']}%")
            
            if 'pressure' in weather_data:
                details.append(f"Pressure: {weather_data['pressure']} hPa")
            
            if 'wind_speed' in weather_data:
                details.append(f"Wind: {weather_data['wind_speed']} m/s")
            
            # Display details
            details_frame = self.details_frame or self.widgets['details_frame']
            if details_frame:
                for i, detail in enumerate(details):
                    detail_label = tk.Label(details_frame, text=detail, 
                                        bg="#1e40af", fg="#9ca3af", 
                                        font=("Segoe UI", 10))
                    detail_label.grid(row=0, column=i, padx=10, sticky="w")
                    
        except Exception as e:
            self.logger.error(f"Error updating weather details: {e}")

    def extract_five_day_summary(self, forecast):       
        forecast_list = forecast.get("list", [])
        daily_data = defaultdict(list)
              
        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if dt_txt:
                date = dt_txt.split(" ")[0]
                daily_data[date].append(entry)

        five_day_forecasts = []
     
        for date in sorted(daily_data.keys())[:5]:
            entries = daily_data[date]
            preferred_entry = next(
                (e for e in entries if "12:00:00" in e["dt_txt"]),
                entries[len(entries)//2]  
            )
            five_day_forecasts.append(preferred_entry)

        return five_day_forecasts

    def display_forecast(self, forecast_list, units="metric"):       
        try:
            forecast_frame = self.widgets['forecast_items_frame']
            if not forecast_frame:
                self.logger.warning("No forecast items frame available")
                return
                
            for widget in forecast_frame.winfo_children():
                widget.destroy()
            
            if not forecast_list:
                error_label = tk.Label(forecast_frame, 
                                    text="⚠️ No forecast data available",
                                    font=("Segoe UI", 12), bg="#374151", fg="#e74c3c")
                error_label.grid(row=0, column=0, columnspan=5, pady=20)
                return        
          
            for i in range(5):
                forecast_frame.grid_columnconfigure(i, weight=1, uniform="forecast")
                  
            forecast_frame.grid_rowconfigure(0, weight=1)
            
            today = datetime.now()
            for i, forecast in enumerate(forecast_list):
                try:
                    day = today + timedelta(days=i)
                    day_name = "Today" if i == 0 else day.strftime("%A")[:3]
                    
                    # Main forecast item frame with fixed height
                    item_frame = tk.Frame(forecast_frame, 
                                        bg="#4b5563", relief="raised", bd=1)
                    item_frame.grid(row=0, column=i, padx=4, pady=5, sticky="nsew", 
                                ipady=10, ipadx=8)
                    item_frame.grid_rowconfigure(0, weight=0)  
                    item_frame.grid_rowconfigure(1, weight=0)  
                    item_frame.grid_rowconfigure(2, weight=0)  
                    item_frame.grid_rowconfigure(3, weight=0)  
                    item_frame.grid_rowconfigure(4, weight=0)  
                    item_frame.grid_rowconfigure(5, weight=1)  
                    item_frame.grid_columnconfigure(0, weight=1)
                               
                    day_label = tk.Label(item_frame, text=day_name, bg="#4b5563", fg="white",
                                    font=("Segoe UI", 11, "bold"), height=1)
                    day_label.grid(row=0, column=0, pady=(8, 5), sticky="ew")
                    
                    # Weather icon with fixed container size
                    icon_frame = tk.Frame(item_frame, bg="#4b5563", height=45, width=45)
                    icon_frame.grid(row=1, column=0, pady=3)
                    icon_frame.grid_propagate(False)  # Maintain fixed size
                    icon_frame.grid_rowconfigure(0, weight=1)
                    icon_frame.grid_columnconfigure(0, weight=1)
                    
                    weather_main = forecast.get("weather", [{}])[0].get("main", "")
                    icon_path = self.get_icon_path(weather_main)

                    try:
                        if icon_path:
                            img = Image.open(icon_path).resize((38, 38), Image.Resampling.LANCZOS)
                            photo = ImageTk.PhotoImage(img)
                            icon_label = tk.Label(icon_frame, image=photo, bg="#4b5563")
                            icon_label.image = photo  # Keep reference
                            icon_label.place(relx=0.5, rely=0.5, anchor="center")
                        else:
                            raise Exception("No icon available")
                    except Exception:
                        emoji = WeatherEmoji.get_weather_emoji(weather_main)
                        emoji_label = tk.Label(icon_frame, text=emoji, bg="#4b5563", 
                                            font=("Segoe UI", 18))
                        emoji_label.place(relx=0.5, rely=0.5, anchor="center")
                    
                    # Weather description with consistent height
                    weather_desc = forecast.get("weather", [{}])[0].get("description", "").title()
                    desc_text = weather_desc if len(weather_desc) <= 12 else weather_desc[:12] + "..."
                    
                    desc_label = tk.Label(item_frame, text=desc_text, bg="#4b5563", fg="#d1d5db",
                                        font=("Segoe UI", 8), height=2, wraplength=75)
                    desc_label.grid(row=2, column=0, pady=(0, 3), sticky="ew")
                                 
                    temp_main = forecast.get('main', {})
                    temp_max = temp_main.get('temp_max', 0)
                    temp_min = temp_main.get('temp_min', 0)               
                
                    unit = "°F" if units == "imperial" else "°C"                
                  
                    high_temp_label = tk.Label(item_frame, 
                                        text=f"{temp_max:.0f}{unit}",
                                        bg="#4b5563", fg="white", 
                                        font=("Segoe UI", 12, "bold"),
                                        height=1)
                    high_temp_label.grid(row=3, column=0, sticky="ew")
                    
                    low_temp_label = tk.Label(item_frame, 
                                        text=f"{temp_min:.0f}{unit}",
                                        bg="#4b5563", fg="#9ca3af", 
                                        font=("Segoe UI", 9),
                                        height=1)
                    low_temp_label.grid(row=4, column=0, pady=(0, 5), sticky="ew")
                    
                    details_frame = tk.Frame(item_frame, bg="#374151", relief="sunken", bd=1)
                    details_frame.grid(row=5, column=0, sticky="ew", padx=3, pady=(3, 8))                
                  
                    details_inner = tk.Frame(details_frame, bg="#374151")
                    details_inner.pack(fill="both", expand=True, padx=2, pady=2)                
                    
                    humidity = temp_main.get('humidity', 0)
                    if humidity > 0:
                        humidity_label = tk.Label(details_inner, text=f"💧 {humidity}%",
                                                bg="#374151", fg="#60a5fa",
                                                font=("Segoe UI", 7))
                        humidity_label.pack(pady=1)                

                    pressure = temp_main.get('pressure', 0)
                    if pressure > 0:
                        pressure_label = tk.Label(details_inner, text=f"🌪️ {pressure}",
                                                bg="#374151", fg="#a78bfa",
                                                font=("Segoe UI", 7))
                        pressure_label.pack(pady=1)                
               
                    feels_like = temp_main.get('feels_like', temp_max)
                    if feels_like != temp_max:
                        feels_like_label = tk.Label(details_inner, text=f"🌡️ {feels_like:.0f}{unit}",
                                                bg="#374151", fg="#fbbf24",
                                                font=("Segoe UI", 7))
                        feels_like_label.pack(pady=1)                
                    
                    wind_data = forecast.get('wind', {})
                    wind_speed = wind_data.get('speed', 0)
                    if wind_speed > 0:
                        wind_unit = "mph" if units == "imperial" else "m/s"
                        wind_label = tk.Label(details_inner, text=f"💨 {wind_speed:.1f}{wind_unit}",
                                            bg="#374151", fg="#34d399",
                                            font=("Segoe UI", 7))
                        wind_label.pack(pady=1)
                    
                    pop = forecast.get('pop', 0) * 100 if 'pop' in forecast else 0
                    if pop > 0:
                        pop_label = tk.Label(details_inner, text=f"☔ {pop:.0f}%",
                                        bg="#374151", fg="#60a5fa",
                                        font=("Segoe UI", 7))
                        pop_label.pack(pady=1)
                    
                except Exception as e:
                    self.logger.error(f"Forecast display error for day {i}: {e}")
                    error_frame = tk.Frame(forecast_frame, 
                                        bg="#ef4444", relief="raised", bd=1)
                    error_frame.grid(row=0, column=i, padx=4, pady=5, sticky="nsew", 
                                ipady=10, ipadx=8)
                    error_frame.grid_rowconfigure(0, weight=1)
                    error_frame.grid_columnconfigure(0, weight=1)
                    
                    tk.Label(error_frame, text="⚠️\nError", bg="#ef4444", fg="white",
                            font=("Segoe UI", 10), justify="center").place(relx=0.5, rely=0.5, anchor="center")

        except Exception as e:
            self.logger.error(f"Error in display_forecast: {e}")

    
    
    def update_hourly_forecast(self, city, country, units):      
        try:
            # Clear existing hourly forecast
            hourly_frame = self.widgets['hourly_scroll_frame']
            if not hourly_frame:
                self.logger.warning("No hourly scroll frame available")
                return
                
            for widget in hourly_frame.winfo_children():
                widget.destroy()

            self.logger.info(f"Fetching hourly forecast for {city}, {country}")
            temp_unit = "°F" if units == "imperial" else "°C"

            # Fetch hourly data
            try:
                hourly_data = self.fetcher.fetch_hourly_forecast(city, country, units)
            except Exception as fetch_error:
                self.logger.error(f"Error fetching hourly data: {fetch_error}")
                hourly_data = None

            if not hourly_data:                
                try:
                    forecast_data = self.fetcher.fetch_five_day_forecast(city, country, units)
                    if forecast_data and 'list' in forecast_data:
                        hourly_data = self.extract_hourly_from_forecast(forecast_data, units)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback hourly data fetch failed: {fallback_error}")

            if not hourly_data:
                error_label = tk.Label(
                    hourly_frame,
                    text="❌ Unable to load hourly forecast\nPlease check your internet connection",
                    font=("Segoe UI", 12),
                    bg="#f8fafc",
                    fg="#e74c3c"
                )
                error_label.pack(pady=20)
                return
                
            icon_mgr = WeatherIconManager()

            for i, hour_data in enumerate(hourly_data):
                try:
                    hour_frame = tk.Frame(hourly_frame, bg="white", relief="solid", bd=1)
                    hour_frame.pack(fill="x", padx=5, pady=2)
                    hour_frame.grid_columnconfigure(3, weight=1)

                 
                    time_12hr = hour_data.get('datetime', datetime.now()).strftime("%I:%M %p")
                    tk.Label(
                        hour_frame,
                        text=time_12hr,
                        font=("Segoe UI", 11, "bold"),
                        bg="white",
                        fg="#1f2937",
                        width=10
                    ).grid(row=0, column=0, padx=5, pady=5)

                    weather_main = hour_data.get("weather", [{}])[0].get("main", "")
                    try:
                        icon_path = icon_mgr.get_icon_path(weather_main)
                        img = Image.open(icon_path).resize((40, 40))
                        photo = ImageTk.PhotoImage(img)
                        icon_label = tk.Label(hour_frame, image=photo, bg="#4b5563")
                        icon_label.image = photo
                    except Exception as e:
                        print(f"[Icon Load Error] {e}")
                        emoji = WeatherEmoji.get_weather_emoji(weather_main)
                        icon_label = tk.Label(hour_frame, text=emoji, bg="#4b5563", font=("Segoe UI", 20))
                    icon_label.grid(row=1, column=0, pady=3)

                    temp = hour_data.get('temp', 0)
                    tk.Label(
                        hour_frame,
                        text=f"{temp:.0f}{temp_unit}",
                        font=("Segoe UI", 12, "bold"),
                        bg="white",
                        fg="#1f2937",
                        width=8
                    ).grid(row=0, column=2, padx=5, pady=5)
                   
                    desc = hour_data.get('weather_desc', '').title()
                    tk.Label(
                        hour_frame,
                        text=desc,
                        font=("Segoe UI", 9),
                        bg="white",
                        fg="#6b7280"
                    ).grid(row=0, column=3, padx=5, pady=5, sticky="w")
                    
                    pop = hour_data.get('pop', 0)
                    if pop > 0:
                        tk.Label(
                            hour_frame,
                            text=f"💧{pop:.0f}%",
                            font=("Segoe UI", 9),
                            bg="white",
                            fg="#3b82f6"
                        ).grid(row=0, column=4, padx=5, pady=5)
                
                    humidity = hour_data.get('humidity', 0)
                    if humidity > 0:
                        tk.Label(
                            hour_frame,
                            text=f"🌫️{humidity}%",
                            font=("Segoe UI", 9),
                            bg="white",
                            fg="#6b7280"
                        ).grid(row=0, column=5, padx=5, pady=5)

                except Exception as hour_error:
                    self.logger.error(f"Error displaying hour {i}: {hour_error}")
                    continue

        except Exception as e:
            self.logger.error(f"Critical error in update_hourly_forecast: {e}")
            hourly_frame = self.widgets['hourly_scroll_frame']
            if hourly_frame:
                error_label = tk.Label(
                    hourly_frame,
                    text="💥 Critical error loading hourly forecast",
                    font=("Segoe UI", 12),
                    bg="#f8fafc",
                    fg="#e74c3c"
                )
                error_label.pack(pady=20)

    def extract_hourly_from_forecast(self, forecast_data, units):      
        try:
            forecast_list = forecast_data.get("list", [])
            hourly_data = []
            
            for entry in forecast_list[:8]:
                dt_txt = entry.get("dt_txt", "")
                if dt_txt:
                    try:
                        dt = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
                        time_str = dt.strftime("%H:%M")
                    except:
                        time_str = dt_txt.split(" ")[1][:5]
                else:
                    time_str = "N/A"
                
                main_data = entry.get('main', {})
                weather_data = entry.get('weather', [{}])[0]
                
                hourly_entry = {
                    'time': time_str,
                    'datetime': dt if dt_txt else datetime.now(),
                    'temp': main_data.get('temp', 0),
                    'weather_main': weather_data.get('main', ''),
                    'weather_desc': weather_data.get('description', ''),
                    'humidity': main_data.get('humidity', 0),
                    'pop': entry.get('pop', 0) * 100  # Convert to percentage
                }
                hourly_data.append(hourly_entry)
            
            return hourly_data
        except Exception as e:
            self.logger.error(f"Error extracting hourly from forecast: {e}")
            return []

    def update_temperature_graph(self, city, country):      
        try:
            graph_container = self.widgets.get('graph_container')
            if not graph_container:
                self.logger.warning("No graph container available")
                return
                
            # Clear existing content
            for widget in graph_container.winfo_children():
                widget.destroy()
            
            self.logger.info(f"Fetching temperature graph data for {city}, {country}")
            
            # ⭐ CRITICAL: Force insert current data if available
            if hasattr(self, 'current_weather_data') and self.current_weather_data:
                try:
                    # Force re-insert to ensure data is in database
                    success = self.db.insert_reading(self.current_weather_data)
                    if success:
                        self.logger.info("Successfully ensured current weather data is in database")
                    else:
                        self.logger.warning("Failed to insert current weather data")
                except Exception as e:
                    self.logger.warning(f"Could not insert current data: {e}")
            
            # ⭐ ENHANCED: Try multiple approaches to get readings
            readings = None
            
            # Method 1: Direct database query with case variations
            for hours in [1, 6, 12, 24, 48, 72, 168, 720, 8760]:  # Start with 1 hour
                try:
                    # Try exact match first
                    readings = self.db.fetch_recent(city, country, hours=hours)
                    self.logger.info(f"Method 1 - {hours}h: Found {len(readings) if readings else 0} readings")
                    
                    # If no exact match, try case variations
                    if not readings or len(readings) == 0:
                        readings = self.db.fetch_recent(city.title(), country.upper(), hours=hours)
                        self.logger.info(f"Method 1b - {hours}h: Found {len(readings) if readings else 0} readings with title/upper case")
                    
                    if not readings or len(readings) == 0:
                        readings = self.db.fetch_recent(city.lower(), country.lower(), hours=hours)
                        self.logger.info(f"Method 1c - {hours}h: Found {len(readings) if readings else 0} readings with lower case")
                    
                    if readings and len(readings) >= 1:  # Changed from > 1 to >= 1
                        self.logger.info(f"Found {len(readings)} readings in last {hours} hours")
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error fetching data for {hours}h range: {e}")
                    continue
            
            # Method 2: Get all readings and filter manually
            if not readings or len(readings) == 0:
                try:
                    self.logger.info("Trying alternative data fetch method - getting all readings")
                    all_readings = self.db.get_all_readings()
                    self.logger.info(f"Total readings in database: {len(all_readings)}")
                    
                    # Filter manually with case-insensitive matching
                    city_lower = city.lower()
                    country_lower = country.lower()
                    
                    matching_readings = []
                    for reading in all_readings:
                        reading_city = reading.get('city', '').lower()
                        reading_country = reading.get('country', '').lower()
                        if reading_city == city_lower and reading_country == country_lower:
                            matching_readings.append(reading)
                    
                    if matching_readings:
                        readings = matching_readings[:50]  # Limit to last 50 readings
                        self.logger.info(f"Found {len(readings)} matching readings via manual filter")
                        
                except Exception as e:
                    self.logger.error(f"Alternative fetch method failed: {e}")
            
            # Method 3: Force a fresh weather fetch if still no data
            if not readings or len(readings) == 0:
                self.logger.info("No historical data found, fetching fresh weather data")
                try:
                    fresh_data = self.fetcher.fetch_current_weather(city, country)
                    if fresh_data:
                        self.db.insert_reading(fresh_data)
                        # Recursive call with short delay
                        self.root.after(1000, lambda: self.update_temperature_graph(city, country))
                        self._show_placeholder_message(graph_container, f"Fetching data for {city}...\nPlease wait...")
                        return
                except Exception as fetch_error:
                    self.logger.error(f"Fresh data fetch failed: {fetch_error}")
            
            # Debug: Show what we found
            if readings:
                self.logger.info(f"Sample reading data: {readings[0] if readings else 'None'}")
                self.logger.info(f"All readings cities: {[r.get('city') for r in readings[:5]]}")
            
            # ⭐ MODIFIED: Show graph even with single data point
            if readings and len(readings) >= 1:  # Changed from > 1 to >= 1            
                import pandas as pd
                import matplotlib.pyplot as plt
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                from matplotlib.dates import DateFormatter, HourLocator
                
                df = pd.DataFrame(readings)
                self.logger.info(f"Processing {len(df)} readings for graph")
                
                # Handle timestamp conversion with multiple formats
                if 'timestamp' in df.columns:
                    try:
                        # Try different timestamp formats
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                        
                        # Remove any rows with invalid timestamps
                        df = df.dropna(subset=['timestamp'])
                        df = df.sort_values('timestamp')
                        
                        if len(df) == 0:
                            raise ValueError("No valid timestamps found")
                        
                        # Create the plot with better error handling
                        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
                        fig.patch.set_facecolor('white')
                                    
                        # Temperature plot with data validation
                        if 'temp' in df.columns and df['temp'].notna().any():
                            temps = df['temp'].astype(float).tolist()
                            temp_unit = "°F" if country.upper() == "US" else "°C"
                            times = df['timestamp'].tolist()
                            
                            self.logger.info(f"Temperature range: {min(temps):.1f} to {max(temps):.1f}{temp_unit}")
                            
                            # ⭐ SINGLE POINT HANDLING: Show point even if only one data point
                            if len(temps) == 1:
                                ax1.scatter(times, temps, color='#ef4444', s=100, zorder=5)
                                ax1.axhline(y=temps[0], color='#ef4444', linestyle='--', alpha=0.5)
                            else:
                                ax1.plot(times, temps, color='#ef4444', linewidth=2, marker='o', markersize=4)
                            
                            ax1.set_ylabel(f'Temperature ({temp_unit})', color='#ef4444', fontsize=10)
                            ax1.tick_params(axis='y', labelcolor='#ef4444')
                            ax1.grid(True, alpha=0.3)
                            ax1.set_title(f'Weather Trends for {city}, {country}', fontsize=12, pad=15)
                            
                            # Add temperature info
                            if len(temps) == 1:
                                temp_info = f"Current: {temps[0]:.1f}°"
                            else:
                                temp_info = f"Range: {min(temps):.1f}° - {max(temps):.1f}°"
                            ax1.text(0.02, 0.98, temp_info, transform=ax1.transAxes, 
                                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                        else:
                            ax1.text(0.5, 0.5, 'No temperature data available', 
                                    transform=ax1.transAxes, ha='center', va='center')
                                        
                        # Second subplot - humidity and/or pressure
                        if 'humidity' in df.columns and df['humidity'].notna().any():
                            humidity = df['humidity'].astype(float).tolist()
                            if len(humidity) == 1:
                                ax2.scatter(times, humidity, color='#3b82f6', s=100, zorder=5)
                                ax2.axhline(y=humidity[0], color='#3b82f6', linestyle='--', alpha=0.5)
                            else:
                                ax2.plot(times, humidity, color='#3b82f6', linewidth=2, marker='s', markersize=3)
                            ax2.set_ylabel('Humidity (%)', color='#3b82f6')
                            ax2.tick_params(axis='y', labelcolor='#3b82f6')
                            
                            # Add pressure on right axis if available
                            if 'pressure' in df.columns and df['pressure'].notna().any():
                                pressure = df['pressure'].astype(float).tolist()
                                ax2_twin = ax2.twinx()
                                if len(pressure) == 1:
                                    ax2_twin.scatter(times, pressure, color='#10b981', s=80, marker='^', zorder=5)
                                    ax2_twin.axhline(y=pressure[0], color='#10b981', linestyle='--', alpha=0.5)
                                else:
                                    ax2_twin.plot(times, pressure, color='#10b981', linewidth=2, marker='^', markersize=3)
                                ax2_twin.set_ylabel('Pressure (hPa)', color='#10b981')
                                ax2_twin.tick_params(axis='y', labelcolor='#10b981')
                        else:
                            ax2.text(0.5, 0.5, f'Additional weather data for {city}\nwill appear as it\'s collected', 
                                    transform=ax2.transAxes, ha='center', va='center', fontsize=11)
                            ax2.set_ylabel('Collecting data...')
                        
                        ax2.grid(True, alpha=0.3)                

                        # Format x-axis based on time span
                        if len(times) >= 1:
                            if len(times) == 1:
                                # Single point - just show the time
                                ax2.xaxis.set_major_formatter(DateFormatter('%H:%M'))
                                ax2.set_xlabel('Time')
                            else:
                                time_span = (max(times) - min(times)).total_seconds() / 3600
                                if time_span <= 24:
                                    ax2.xaxis.set_major_formatter(DateFormatter('%H:%M'))
                                    ax2.set_xlabel('Time')
                                elif time_span <= 168:  # 1 week
                                    ax2.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
                                    ax2.set_xlabel('Date & Time')
                                else:
                                    ax2.xaxis.set_major_formatter(DateFormatter('%m/%d'))
                                    ax2.set_xlabel('Date')
                                    
                            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
                        
                        fig.tight_layout()                

                        canvas = FigureCanvasTkAgg(fig, graph_container)
                        canvas.draw()
                        canvas.get_tk_widget().pack(fill='both', expand=True)
                        
                        self.logger.info(f"Temperature graph successfully updated for {city}")
                        
                    except Exception as timestamp_error:
                        self.logger.error(f"Timestamp processing error: {timestamp_error}")
                        self._show_error_message(graph_container, f"Data format error: {timestamp_error}")
                        
                else:
                    self.logger.error("No timestamp column found in data")
                    self._show_error_message(graph_container, "Data format error: No timestamps")
                        
            else:
                self.logger.info(f"No data available for {city} graph: {len(readings) if readings else 0} readings")
                
                # Show helpful message with data collection info
                message = f"Collecting weather data for {city}...\n"
                if readings:
                    message += f"({len(readings)} reading{'s' if len(readings) != 1 else ''} so far)\n"
                else:
                    message += "(0 readings so far)\n"
                message += "Graph will appear after data collection."
                
                self._show_placeholder_message(graph_container, message)
                
        except Exception as e:
            self.logger.error(f"Error updating temperature graph: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            if self.widgets.get('graph_container'):
                self._show_error_message(self.widgets['graph_container'], f"Graph error: {str(e)}")


    # Helper method for placeholder messages
    def _show_placeholder_message(self, container, message):
        """Show a placeholder message in the graph container"""
        try:
            import tkinter as tk
            
            # Clear container
            for widget in container.winfo_children():
                widget.destroy()
            
            # Create message label
            message_label = tk.Label(
                container, 
                text=message,
                font=("Segoe UI", 12),
                fg="#64748b",
                bg="white",
                justify=tk.CENTER
            )
            message_label.pack(expand=True, fill='both')
            
        except Exception as e:
            self.logger.error(f"Error showing placeholder message: {e}")

    def _show_error_message(self, container, message):
        """Show an error message in the graph container"""
        try:
            import tkinter as tk
            
            # Clear container
            for widget in container.winfo_children():
                widget.destroy()
            
            # Create error label
            error_label = tk.Label(
                container, 
                text=f"⚠️ {message}",
                font=("Segoe UI", 11),
                fg="#dc2626",
                bg="white",
                justify=tk.CENTER
            )
            error_label.pack(expand=True, fill='both')
            
        except Exception as e:
            self.logger.error(f"Error showing error message: {e}")
 
    def get_widget(self, widget_name):       
        return self.widgets.get(widget_name)

    def clear_widget(self, widget_name):       
        widget = self.widgets.get(widget_name)
        if widget:
            for child in widget.winfo_children():
                child.destroy()

    def get_current_weather_data(self):       
        """Get the currently stored weather data"""
        return self.current_weather_data
    
    def get_current_location(self):
        """Get current city and country"""
        city = self.city_entry.get().strip() if self.city_entry else "Knoxville"
        country = self.country_entry.get().strip() if self.country_entry else "US"
        return city, country
