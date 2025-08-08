import threading
import tkinter as tk
from tkinter import messagebox
from collections import defaultdict
from datetime import datetime, timedelta
import time
from features.weather_icons import WeatherIconManager
from features.emoji import WeatherEmoji
from PIL import Image, ImageTk
from utils.date_time_utils import format_local_time
class GetWeather:
      
    def __init__(self, fetcher, db, logger, root=None):
        self.fetcher = fetcher
        self.db = db
        self.logger = logger
        self.root = root
        self.current_weather_data = None
        
        self.widgets = {}
        self.display_component = None
        # UI widget references - these will be set by the main app
        self.city_entry = None
        self.country_entry = None
        self.temp_label = None
        self.city_label = None
        self.desc_label = None
        self.icon_label = None
        self.details_frame = None
        self.forecast_items_frame = None
        self.hourly_scroll_frame = None
        self.graph_container = None
        
        # Reference to display components
        self.display_component = None
        
        # Callbacks for UI updates - components can register these
        self.ui_callbacks = {
            'on_weather_start': [],
            'on_weather_success': [],
            'on_weather_error': [],
            'on_forecast_success': []
        }
    
    def set_ui_references(self, city_entry=None, country_entry=None, temp_label=None, 
                         city_label=None, desc_label=None, icon_label=None,
                         details_frame=None, forecast_items_frame=None,
                         hourly_scroll_frame=None, graph_container=None):
        """Set references to UI widgets"""
        if city_entry:
            self.city_entry = city_entry
        if country_entry:
            self.country_entry = country_entry
        if temp_label:
            self.temp_label = temp_label
        if city_label:
            self.city_label = city_label
        if desc_label:
            self.desc_label = desc_label
        if icon_label:
            self.icon_label = icon_label
        if details_frame:
            self.details_frame = details_frame
        if forecast_items_frame:
            self.forecast_items_frame = forecast_items_frame
        if hourly_scroll_frame:
            self.hourly_scroll_frame = hourly_scroll_frame
        if graph_container:
            self.graph_container = graph_container
    
    def set_display_component(self, display_component):
        """Set the display component for UI updates"""
        self.display_component = display_component
    
    def register_callback(self, event_type, callback):
        """Register a callback function for weather events"""
        if event_type in self.ui_callbacks:
            self.ui_callbacks[event_type].append(callback)
    
    def _trigger_callbacks(self, event_type, *args, **kwargs):
        for callback in self.ui_callbacks.get(event_type, []):
            try:
                if self.root:
                    self.root.after(0, lambda: callback(*args, **kwargs))
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error for {event_type}: {e}")

    def get_weather_threaded(self, city=None, country=None):    
        threading.Thread(target=self.get_weather, args=(city, country), daemon=True).start()
    
    
    def set_widgets(self, widgets_dict):
        """Set all widget references at once"""
        self.widgets.update(widgets_dict)
   
    def get_weather(self, city=None, country=None):        
        try:           
            if city is None:
                city = self.widgets.get('city_entry').get().strip() if self.widgets.get('city_entry') else "Knoxville"
            if country is None:
                country = self.widgets.get('country_entry').get().strip() if self.widgets.get('country_entry') else "US"
                    
            units = "imperial" if country.upper() == "US" else "metric"
            
            self.logger.info(f"Fetching weather for {city}, {country} with units: {units}")
            
            # Trigger loading callbacks
            self._trigger_callbacks('on_weather_start', city, country)
            
            # Update UI to show loading
            if self.root and self.widgets.get('temp_label'):
                self.root.after(0, lambda: self.widgets['temp_label'].config(text="Loading..."))
            if self.root and self.widgets.get('city_label'):
                self.root.after(0, lambda: self.widgets['city_label'].config(text=f"Loading {city}, {country}..."))
            
            # Fetch current weather with retry logic
            current_weather = None
            for attempt in range(3):
                try:
                    self.logger.info(f"Weather fetch attempt {attempt + 1}")
                    current_weather = self.fetcher.fetch_current_weather(city, country, units)
                    if current_weather:
                        self.logger.info("Weather data fetched successfully")
                        break
                    else:
                        self.logger.warning(f"Attempt {attempt + 1}: No weather data returned")
                except Exception as attempt_error:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {attempt_error}")
                    if attempt == 2:
                        raise attempt_error
                    time.sleep(1)
            
            if current_weather:
                self.current_weather_data = current_weather
                self.logger.info(f"Current weather data: {current_weather}")
                
                # Insert into database FIRST - this is critical for the graph
                try:
                    self.db.insert_reading(current_weather)
                    self.logger.info("Weather data inserted into database")
                except Exception as db_error:
                    self.logger.error(f"Database insert failed: {db_error}")
                
                # Trigger success callbacks BEFORE graph update
                self._trigger_callbacks('on_weather_success', current_weather, units)
                
                # ⭐ CRITICAL FIX: Update temperature graph with longer delay to ensure DB insert completes
                if self.root and self.widgets.get('graph_container'):
                    self.logger.info(f"Scheduling temperature graph update for {city}, {country}")
                    # Use longer delay and ensure city/country are captured in closure
                    def update_graph():
                        try:
                            self.logger.info(f"Executing temperature graph update for {city}, {country}")
                            self.update_temperature_graph(city, country)
                        except Exception as e:
                            self.logger.error(f"Graph update error: {e}")
                    
                    self.root.after(500, update_graph)  # Increased delay from 100ms to 500ms
                
                # Fetch and display forecast
                try:
                    forecast_data = self.fetcher.fetch_five_day_forecast(city, country, units)
                    if forecast_data:
                        daily_forecasts = self.extract_five_day_summary(forecast_data)
                        self._trigger_callbacks('on_forecast_success', daily_forecasts, units)
                        self.logger.info("Forecast data processed successfully")
                except Exception as forecast_error:
                    self.logger.error(f"Forecast fetch failed: {forecast_error}")
                
                # Update hourly forecast
                try:
                    if self.root:
                        self.root.after(0, lambda: self.update_hourly_forecast(city, country, units))
                except Exception as hourly_error:
                    self.logger.error(f"Hourly forecast update failed: {hourly_error}")
                    
            else:
                error_msg = f"Could not fetch weather data for {city}, {country}. Please check the city name and try again."
                self.logger.error(error_msg)
                self._trigger_callbacks('on_weather_error', error_msg)
                
                if self.root:
                    self.root.after(0, lambda: messagebox.showerror("Weather Fetch Error", error_msg))
                    
        except Exception as e:
            self.logger.error(f"Critical weather fetch error: {e}")
            error_msg = f"Weather service unavailable: {str(e)}"
            self._trigger_callbacks('on_weather_error', error_msg)
            
            if self.root:
                self.root.after(0, lambda: messagebox.showerror("Connection Error", error_msg))


   
    def refresh_for_location(self, city, country):
            """Refresh weather data for a specific location"""
            self.get_weather_threaded(city, country)
   
   
    def extract_five_day_summary(self, forecast):
        """Extract 5-day forecast summary from API response"""
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
                entries[len(entries)//2]  # fallback to middle of the day
            )
            five_day_forecasts.append(preferred_entry)

        return five_day_forecasts
    
    def get_current_weather_data(self):
        """Get the last fetched weather data"""
        return self.current_weather_data
    
    def refresh_weather(self, city=None, country=None):
        """Refresh weather data (alias for get_weather_threaded)"""
        self.get_weather_threaded(city, country)

    def extract_hourly_from_forecast(self, forecast_data, units):
        """Extract hourly data from forecast response"""
        try:
            forecast_list = forecast_data.get("list", [])
            hourly_data = []            
           
            for entry in forecast_list[:8]:
                dt_txt = entry.get("dt_txt", "")
                if dt_txt:                   
                    try:
                        dt = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
                        time_str = dt.strftime("%I:%M %p")
                    except:
                        time_str = dt_txt.split(" ")[1][:5]
                else:
                    time_str = "N/A"                
                main_data = entry.get('main', {})
                weather_data = entry.get('weather', [{}])[0]
                
                hourly_entry = {
                    'time': time_str,
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
   
    def update_hourly_forecast(self, city, country, units):
        try:           
            scroll_frame = None
            
            if hasattr(self, 'hourly_scroll_frame') and self.hourly_scroll_frame:
                scroll_frame = self.hourly_scroll_frame
            else:
                self.logger.warning("hourly_scroll_frame is not set — forecast update skipped.")
                return
           
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            self.logger.info(f"Fetching hourly forecast for {city}, {country}")
            temp_unit = "°F" if units == "imperial" else "°C"

            try:
                hourly_data = self.fetcher.fetch_hourly_forecast(city, country, units)
                print(f"DEBUG: hourly_data type: {type(hourly_data)}")
                if hourly_data:
                    print(f"DEBUG: hourly_data length: {len(hourly_data)}")
                    print(f"DEBUG: First item keys: {list(hourly_data[0].keys()) if len(hourly_data) > 0 else 'No items'}")
                    print(f"DEBUG: First item sample: {hourly_data[0] if len(hourly_data) > 0 else 'No items'}")
            except Exception as fetch_error:
                self.logger.error(f"Error fetching hourly data: {fetch_error}")
                hourly_data = None

            if not hourly_data:
                try:
                    forecast_data = self.fetcher.fetch_five_day_forecast(city, country, units)
                    if forecast_data and 'list' in forecast_data:
                        hourly_data = self.extract_hourly_from_forecast(forecast_data, units)
                        print(f"DEBUG: Fallback hourly_data length: {len(hourly_data) if hourly_data else 'None'}")
                except Exception as fallback_error:
                    self.logger.error(f"Fallback hourly data fetch failed: {fallback_error}")

            if not hourly_data:
                error_label = tk.Label(
                    scroll_frame,
                    text="❌ Unable to load hourly forecast\nPlease check your internet connection",
                    font=("Segoe UI", 12),
                    bg="#f8fafc",
                    fg="#e74c3c"
                )
                error_label.pack(pady=20)
                return
           
            container_frame = tk.Frame(scroll_frame, bg="#f8fafc")
            container_frame.pack(fill="x", expand=False, padx=5, pady=5)
            num_cards = min(len(hourly_data), 8)     
            card_width = 105 
            card_height = 160         
            card_spacing = 4  

            try:
                from features.weather_icons import WeatherIconManager
                icon_mgr = WeatherIconManager()
            except ImportError:
                icon_mgr = None
                self.logger.warning("WeatherIconManager not available")

            try:
                from features.emoji import WeatherEmoji
            except ImportError:
                WeatherEmoji = None
                self.logger.warning("WeatherEmoji not available")
          
            def format_time_for_display(time_str):                
                try:
                    print(f"DEBUG: Input time_str: '{time_str}' (type: {type(time_str)})")
                    
                    # Handle different input types
                    if not time_str:
                        print("DEBUG: Empty time_str, returning 'N/A'")
                        return "N/A"
                    
                    from datetime import datetime
                    import pytz
                    
                    # Try different parsing approaches
                    dt = None                    
                
                    if isinstance(time_str, datetime):
                        dt = time_str
                        print(f"DEBUG: Input is datetime object: {dt}")
                                     
                    elif isinstance(time_str, str):
                        formats_to_try = [
                            "%Y-%m-%d %H:%M:%S",  
                            "%Y-%m-%d %H:%M",     
                            "%H:%M:%S",         
                            "%H:%M",            
                            "%I:%M %p",          
                            "%I %p",             
                        ]
                        
                        for fmt in formats_to_try:
                            try:
                                dt = datetime.strptime(time_str, fmt)
                                print(f"DEBUG: Parsed with format '{fmt}': {dt}")
                                break
                            except ValueError:
                                continue
                        
                        # If standard parsing failed, try dateutil parser
                        if dt is None:
                            try:
                                from dateutil import parser as date_parser
                                dt = date_parser.parse(time_str)
                                print(f"DEBUG: Parsed with dateutil: {dt}")
                            except Exception as e:
                                print(f"DEBUG: dateutil parsing failed: {e}")
                    
                    if dt is None:
                        print(f"DEBUG: Could not parse time, returning truncated original: '{time_str[:8]}'")
                        return time_str[:8] if len(time_str) > 8 else time_str
                                     
                    try:                      
                        if dt.tzinfo is None:
                            utc = pytz.UTC
                            dt = utc.localize(dt)
                            print(f"DEBUG: Localized to UTC: {dt}")                        
                        
                        eastern = pytz.timezone('America/New_York')
                        eastern_time = dt.astimezone(eastern)
                        print(f"DEBUG: Converted to Eastern: {eastern_time}")                        
                      
                        if eastern_time.minute == 0:
                            formatted = eastern_time.strftime('%I %p').lstrip('0')
                        else:
                            formatted = eastern_time.strftime('%I:%M %p').lstrip('0')
                        
                        print(f"DEBUG: Final formatted time: '{formatted}'")
                        return formatted
                        
                    except Exception as tz_error:
                        print(f"DEBUG: Timezone conversion error: {tz_error}")
                        # Fallback to simple format
                        if dt.minute == 0:
                            return dt.strftime('%I %p').lstrip('0')
                        else:
                            return dt.strftime('%I:%M %p').lstrip('0')
                        
                except Exception as e:
                    print(f"DEBUG: Time formatting error: {e}")
                    self.logger.warning(f"Time formatting error: {e}")
                    # Return a safe fallback
                    return str(time_str)[:8] if time_str else "N/A"
        
            for i, hour_data in enumerate(hourly_data[:num_cards]):
                try:
                    print(f"DEBUG: Processing card {i}, hour_data keys: {list(hour_data.keys())}")                    
                  
                    hour_card = tk.Frame(
                        container_frame, 
                        bg="#4b5563", 
                        relief="solid", 
                        bd=1, 
                        width=card_width, 
                        height=card_height
                    )
                    hour_card.pack(side="left", padx=card_spacing, pady=2, fill="y")
                    hour_card.pack_propagate(False)                      
                   
                    inner_frame = tk.Frame(hour_card, bg="#4b5563")
                    inner_frame.pack(fill="both", expand=True, padx=4, pady=4)                  
                    time_display = None
                    for time_field in ['datetime', 'dt_txt', 'time', 'dt']:
                        if time_field in hour_data:
                            time_display = hour_data[time_field]
                            print(f"DEBUG: Found time in field '{time_field}': {time_display}")
                            break
                    
                    if time_display is None:
                        time_display = "N/A"
                        print(f"DEBUG: No time field found, using 'N/A'")
                    
                    time_eastern = format_time_for_display(time_display)
                    print(f"DEBUG: Final time_eastern for display: '{time_eastern}'")
                    
                    time_label = tk.Label(
                        inner_frame,
                        text=time_eastern,
                        font=("Segoe UI", 8, "bold"),
                        bg="#4b5563",
                        fg="white"
                    )
                    time_label.pack(pady=(0, 4))

                    # 🌤️ Weather icon (centered and uniform size)
                    weather_main = hour_data.get("weather_main", "")
                    print(f"DEBUG: weather_main: '{weather_main}'")
                    
                    icon_loaded = False
                    if icon_mgr:
                        try:
                            from PIL import Image, ImageTk
                            icon_path = icon_mgr.get_icon_path(weather_main)
                            img = Image.open(icon_path).resize((32, 32))                          
                            photo = ImageTk.PhotoImage(img)
                            icon_label = tk.Label(inner_frame, image=photo, bg="#4b5563")
                            icon_label.image = photo  # Keep reference
                            icon_loaded = True
                        except Exception as e:
                            self.logger.warning(f"[Icon Load Error] {e}")
                    
                    if not icon_loaded:
                        if WeatherEmoji:
                            emoji = WeatherEmoji.get_weather_emoji(weather_main)
                            icon_label = tk.Label(inner_frame, text=emoji, font=("Segoe UI", 16), bg="#4b5563")
                        else:
                            # Final fallback to simple text
                            weather_text = weather_main[:3].upper() if weather_main else "N/A"
                            icon_label = tk.Label(inner_frame, text=weather_text, font=("Segoe UI", 9, "bold"), 
                                                bg="#4b5563", fg="white")

                    icon_label.pack(pady=(0, 4))
                   
                    desc = hour_data.get('weather_desc', '').title()
                    if len(desc) > 10:  
                        desc = desc[:8] + "..."
                    desc_label = tk.Label(
                        inner_frame,
                        text=desc,
                        font=("Segoe UI", 7),
                        bg="#4b5563",
                        fg="lightgray",
                        wraplength=85,
                        justify="center"
                    )
                    desc_label.pack(pady=(0, 4))
                  
                    temp = hour_data.get('temp', 0)
                    print(f"DEBUG: temp: {temp}")
                    temp_label = tk.Label(
                        inner_frame,
                        text=f"{temp:.0f}°",
                        font=("Segoe UI", 11, "bold"),
                        bg="#4b5563",
                        fg="white"
                    )
                    temp_label.pack(pady=(0, 2))
                   
                    pop = hour_data.get('pop', 0)
                    if pop > 0:
                        precip_label = tk.Label(
                            inner_frame,
                            text=f"{pop:.0f}%",
                            font=("Segoe UI", 7),
                            bg="#4b5563",
                            fg="#87ceeb"  
                        )
                        precip_label.pack()

                except Exception as hour_error:
                    self.logger.error(f"Error displaying hour {i}: {hour_error}")
                    print(f"DEBUG: Error displaying hour {i}: {hour_error}")
                    continue

            # Update scroll region after all cards are added
            container_frame.update_idletasks()
            scroll_frame.update_idletasks()

        except Exception as e:
            self.logger.error(f"Critical error in update_hourly_forecast: {e}")
            print(f"DEBUG: Critical error in update_hourly_forecast: {e}")
            
            # Get scroll frame for error display
            scroll_frame = None
            if hasattr(self, 'hourly_scroll_frame') and self.hourly_scroll_frame:
                scroll_frame = self.hourly_scroll_frame
                
            if scroll_frame:
                error_label = tk.Label(
                    scroll_frame,
                    text="💥 Critical error loading hourly forecast",
                    font=("Segoe UI", 12),
                    bg="#f8fafc",
                    fg="#e74c3c"
                )
                error_label.pack(pady=20)