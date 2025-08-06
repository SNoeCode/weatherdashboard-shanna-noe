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
    
    def display_current_weather(self, weather_data):
        try:        
            temp = weather_data.get("temperature", 0)
            temp_unit = weather_data.get("temp_unit", "°F")
            
            # Display temperature 
            # self.temp_label.config(text=f"{temp:.0f}{temp_unit}")
            self.city_label.config(text=f"{weather_data.get('city', 'Unknown')}")
            self.desc_label.config(text=weather_data.get('weather_detail', '').title())
   
            weather_main = weather_data.get("weather_summary", "Clear")
            icon_path = self.get_icon_path(weather_main)
            
            try:
                img = Image.open(icon_path).resize((80, 80))
                photo = ImageTk.PhotoImage(img)
                self.icon_label.config(image=photo, text="")
                self.icon_label.image = photo
            except Exception as e:
                # Fallback to emoji
                emoji_map = {
                    "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️", 
                    "Thunderstorm": "⛈️", "Snow": "🌨️", "Mist": "🌫️"
                }
                emoji = emoji_map.get(weather_main, "❓")
                self.icon_label.config(text=emoji, image="")
            
            # Update weather details
            self.update_weather_details(weather_data)
            
        except Exception as e:
            self.logger.error(f"Error displaying weather: {e}")

    def update_weather_details(self, weather_data):     
        # Clear existing details
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
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
        for i, detail in enumerate(details):
            detail_label = tk.Label(self.widgets['details_frame'], text=detail, 
                                bg="#1e40af", fg="#9ca3af", 
                                font=("Segoe UI", 10))
            detail_label.grid(row=0, column=i, padx=10, sticky="w")

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
        for widget in self.widgets['forecast_items_frame'].winfo_children():
            widget.destroy()
        
        if not forecast_list:
            error_label = tk.Label(self.widgets['forecast_items_frame'], 
                                text="⚠️ No forecast data available",
                                font=("Segoe UI", 12), bg="#374151", fg="#e74c3c")
            error_label.grid(row=0, column=0, columnspan=5, pady=20)
            return        
      
        for i in range(5):
            self.widgets['forecast_items_frame'].grid_columnconfigure(i, weight=1, uniform="forecast")
              
        self.widgets['forecast_items_frame'].grid_rowconfigure(0, weight=1)
        
        today = datetime.now()
        for i, forecast in enumerate(forecast_list):
            try:
                day = today + timedelta(days=i)
                day_name = "Today" if i == 0 else day.strftime("%A")[:3]
                
                # Main forecast item frame with fixed height
                item_frame = tk.Frame(self.widgets['forecast_items_frame'], 
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
                icon_mgr = WeatherIconManager()
                icon_path = icon_mgr.get_icon_path(weather_main)

                try:
                    img = Image.open(icon_path).resize((38, 38), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    icon_label = tk.Label(icon_frame, image=photo, bg="#4b5563")
                    icon_label.image = photo  # Keep reference
                    icon_label.place(relx=0.5, rely=0.5, anchor="center")
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
                error_frame = tk.Frame(self.widgets['forecast_items_frame'], 
                                    bg="#ef4444", relief="raised", bd=1)
                error_frame.grid(row=0, column=i, padx=4, pady=5, sticky="nsew", 
                            ipady=10, ipadx=8)
                error_frame.grid_rowconfigure(0, weight=1)
                error_frame.grid_columnconfigure(0, weight=1)
                
                tk.Label(error_frame, text="⚠️\nError", bg="#ef4444", fg="white",
                        font=("Segoe UI", 10), justify="center").place(relx=0.5, rely=0.5, anchor="center")


                
    def update_hourly_forecast(self, city, country, units):      
        try:
            # Clear existing hourly forecast
            for widget in self.widgets['hourly_scroll_frame'].winfo_children():
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
                    self.widgets['hourly_scroll_frame'],
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
                    hour_frame = tk.Frame(self.widgets['hourly_scroll_frame'], bg="white", relief="solid", bd=1)
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
            if self.widgets['hourly_scroll_frame']:
                error_label = tk.Label(
                    self.widgets['hourly_scroll_frame'],
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
            for widget in self.widgets['graph_container'].winfo_children():
                widget.destroy()
            
            # Get recent readings from database
            readings = self.db.fetch_recent(city, country, hours=24)
            
            if readings and len(readings) > 1:             
                df = pd.DataFrame(readings)                
             
                if 'timestamp' in df.columns:
                    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                        try:
                            df['timestamp'] = pd.to_datetime(df['timestamp'])
                        except:
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                             
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 4), sharex=True)
                               
                temps = df['temp'].tolist()
                temp_unit = "°F" if country.upper() == "US" else "°C"
                times = df['timestamp'].tolist()
                              
                ax1.plot(times, temps, color='#ef4444', linewidth=2, marker='o', markersize=3)
                ax1.set_ylabel(f'Temperature ({temp_unit})', color='#ef4444')
                ax1.tick_params(axis='y', labelcolor='#ef4444')
                ax1.grid(True, alpha=0.3)
                ax1.set_title('Weather Metrics - Last 24 Hours', fontsize=10, pad=10)
                              
                if 'humidity' in df.columns and 'pressure' in df.columns:
                    humidity = df['humidity'].tolist()
                    pressure = df['pressure'].tolist()                    
                  
                    color = '#3b82f6'
                    ax2.plot(times, humidity, color=color, linewidth=2, marker='s', markersize=3)
                    ax2.set_ylabel('Humidity (%)', color=color)
                    ax2.tick_params(axis='y', labelcolor=color)
                                       
                    ax2_twin = ax2.twinx()
                    color = '#10b981'
                    ax2_twin.plot(times, pressure, color=color, linewidth=2, marker='^', markersize=3)
                    ax2_twin.set_ylabel('Pressure (hPa)', color=color)
                    ax2_twin.tick_params(axis='y', labelcolor=color)
                else:                  
                    if 'humidity' in df.columns:
                        humidity = df['humidity'].tolist()
                        ax2.plot(times, humidity, color='#3b82f6', linewidth=2, marker='s', markersize=3)
                        ax2.set_ylabel('Humidity (%)')
                    else:
                        ax2.text(0.5, 0.5, 'Additional data unavailable', 
                                transform=ax2.transAxes, ha='center', va='center')
                
                ax2.grid(True, alpha=0.3)                
               
                ax2.xaxis.set_major_formatter(DateFormatter('%H:%M'))
                ax2.xaxis.set_major_locator(HourLocator(interval=6))
                           
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
                
                fig.tight_layout()                
               
                canvas = FigureCanvasTkAgg(fig, self.widgets['graph_container'])
                canvas.draw()
                canvas.get_tk_widget().pack(fill='both', expand=True)
                
            else:              
                placeholder = tk.Label(self.widgets['graph_container'],
                                    text="📊 Weather metrics will appear\nafter more data is collected",
                                    font=("Segoe UI", 12), bg="white", fg="#6b7280")
                placeholder.pack(expand=True)
                
        except Exception as e:
            self.logger.error(f"Error updating graph: {e}")
            error_label = tk.Label(self.widgets['graph_container'],
                                text="Graph temporarily unavailable",
                                font=("Segoe UI", 12), bg="white", fg="#e74c3c")
            error_label.pack(expand=True)

    def get_widget(self, widget_name):       
        return self.widgets.get(widget_name)

    def clear_widget(self, widget_name):       
        widget = self.widgets.get(widget_name)
        if widget:
            for child in widget.winfo_children():
                child.destroy()

    def get_current_weather_data(self):       
        return self.current_weather_data
    
    
    def display_current_weather(self, weather_data):
        try:       
            temp = weather_data.get("temperature", 0)
            temp_unit = weather_data.get("temp_unit")
            if not temp_unit:
                country = self.country_entry.get().strip() or "US"
                temp_unit = "°F" if country.upper() == "US" else "°C"

            # Display temperature
            self.temp_label.config(text=f"{temp:.0f}{temp_unit}")
            self.city_label.config(text=f"{weather_data.get('city', 'Unknown')}")
            self.desc_label.config(text=weather_data.get('weather_detail', '').title())

            # Update summary
            humidity = weather_data.get("humidity", "N/A")
            wind_speed = weather_data.get("wind_speed", "N/A")
            summary = (
                f"It's currently {temp:.0f}{temp_unit} in {weather_data.get('city', 'your area')}, "
                f"with {weather_data.get('weather_detail', '').lower()} conditions. "
                f"Humidity: {humidity}%, Wind Speed: {wind_speed} km/h."
            )
            self.summary_label.config(text=summary)

            icon_mgr = WeatherIconManager()
            weather_main = weather_data.get("weather_summary", "Clear")
            icon_path = icon_mgr.get_icon_path(weather_main)
            emoji = WeatherEmoji.get_weather_emoji(weather_main)

            try:
                img = Image.open(icon_path).resize((80, 80))
                photo = ImageTk.PhotoImage(img)
                self.icon_label.config(image=photo, text="")
                self.icon_label.image = photo  # type: ignore
            except Exception as e:               
                self.icon_label.config(text=emoji, image="")

            self.update_weather_details(weather_data)

        except Exception as e:
            self.logger.error(f"Error displaying weather: {e}")