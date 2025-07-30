from typing import Dict, Optional, Union, List, Callable
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import os
from matplotlib.container import BarContainer
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter, HourLocator
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import pandas as pd
from matplotlib.dates import DateFormatter, HourLocator
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dotenv import load_dotenv
from config import Config
from config import setup_logger
from typing import cast, Optional
from features.activity.activity_panel import ActivityPanel
from features.simple_statistics import get_weather_stats
from features.weather_icons import display_weather_with_icon, get_icon_path, icon_map
from features.simple_statistics import SimpleStatsPanel
import requests
from weather_data_fetcher import WeatherDataFetcher
from features.city_comparisons import CityComparisonPanel
from features.favorites_manager import FavoriteCityPanel
from features.theme_switcher import ThemeManager
from features.activity.activity_suggester import ActivitySuggester
from features.tomorrows_guess import TomorrowGuessPanel
from features.weather_journal import JournalPanel
from features.trends import TrendPanel
from utils.date_time_utils import format_local_time
from features.graphs_and_charts import WeatherGraphs, GraphsAndChartsPanel
from utils.emoji import WeatherEmoji
from services.weather_stats import get_weather_stats
from features.theme_switcher import ThemeManager
from services.weather_stats import get_weather_stats
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
    
    def show_activity_detail(self, activity):    
        messagebox.showinfo("Activity Suggestion", 
                            f"Great choice! {activity} is perfect for today's weather conditions.\n\n"
                            f"Enjoy your activity and stay safe!")
    state_entry: Optional[ttk.Entry]
    get_city_callback: Optional[Callable]
    # def display_statistics(self):     
    #     try:
    #         city = self.city_entry.get().strip() if self.city_entry else "Knoxville"
    #         country = self.country_entry.get().strip() if self.country_entry else "US"
            
    #         # Get statistics using imported function
    #         stats_text = get_weather_stats(self.db, city, country)
            
    #         # Update display
    #         if self.stats_label:
    #             self.stats_label.config(text=f"📊 Statistics for {city}, {country}:\n\n{stats_text}")
            
    #     except Exception as e:
    #         self.logger.error(f"Error showing statistics: {e}")
    #         if self.stats_label:
    #             self.stats_label.config(text=f"Error loading statistics: {str(e)}")
    
    def display_activity_detail(self, activity):    
        messagebox.showinfo("Activity Suggestion", 
                            f"Great choice! {activity} is perfect for today's weather conditions.\n\n"
                            f"Enjoy your activity and stay safe!")
        
    # def display_statistics(self):     
    #     try:
    #         city = self.city_entry.get().strip() if self.city_entry else "Knoxville"
    #         country = self.country_entry.get().strip() if self.country_entry else "US"
    #         state = self.state_entry.get().strip() or "TN"  # Or however you're retrieving the state
            
    #         # Get statistics using imported function
    #         stats_text = get_weather_stats(self.db, city, state, country)
            
    #         # Update display
    #         if self.stats_label:
    #             self.stats_label.config(text=f"📊 Statistics for {city}, {country}:\n\n{stats_text}")
            
    #     except Exception as e:
    #         self.logger.error(f"Error showing statistics: {e}")
    #         if self.stats_label:
    #             self.stats_label.config(text=f"Error loading statistics: {str(e)}")
    
    # def display_statistics(self) -> None:
    #     """Display weather statistics based on user input fields."""
    #     try:
    #         # Validate that input fields exist
    #         if not all([self.city_entry, self.state_entry, self.country_entry, self.stats_label]):
    #             self.logger.error("One or more input widgets are not initialized.")
    #             if self.stats_label:
    #                 self.stats_label.config(text="Error: Input fields not initialized.")
    #             return

    #         # Safely retrieve values from UI
    #         city = self.city_entry.get().strip() or "Knoxville"
    #         state = self.state_entry.get().strip() or "TN"
    #         country = self.country_entry.get().strip() or "US"

    #         # Get statistics using external function
    #         stats_text = get_weather_stats(self.db, city, state, country)

    #         # Update label or text widget with stats
    #         self.stats_label.config(text=f"📊 Statistics for {city}, {state}, {country}:\n\n{stats_text}")

    #     except Exception as e:
    #         self.logger.error(f"Error displaying statistics: {e}")
    #         if self.stats_label:
    #             self.stats_label.config(text=f"Error loading statistics: {str(e)}")
    def display_statistics(self) -> None:
        """Display weather statistics based on entry fields."""
        try:
            if not all([
                self.city_entry, self.state_entry,
                self.country_entry, self.stats_label
            ]):
                self.logger.error("One or more input fields are not initialized.")
                self.stats_label.config(text="❌ Error: Missing input fields.")
                return

            city = self.city_entry.get().strip() or "Knoxville"
            state = self.state_entry.get().strip() or "TN"
            country = self.country_entry.get().strip() or "US"

            stats_text = get_weather_stats(self.db, city, state, country)
            self.stats_label.config(
                text=f"📊 Statistics for {city}, {state}, {country}:\n\n{stats_text}"
            )

        except Exception as e:
            self.logger.error(f"Error displaying statistics: {e}")
            self.stats_label.config(text=f"❌ Error: {str(e)}")
            
            
    def show_statistics(self) -> None:
        """Show weather statistics in the manual stats display."""
        try:
            city = self.get_city_callback()
            state = "TN"  # Update with dynamic value if needed
            country = "US"

            stats_text = get_weather_stats(self.db, city, state, country)

            if self.stats_label:
                self.stats_label.config(
                    text=f"📊 Statistics for {city}, {state}, {country}:\n\n{stats_text}"
                )

        except Exception as e:
            self.logger.error(f"Error showing statistics: {e}")
            if self.stats_label:
                self.stats_label.config(text=f"Error loading statistics: {str(e)}")
    def display_current_weather(self, weather_data):
        try:
            # Get temperature 
            temp = weather_data.get("temperature", 0)            
            temp_unit = weather_data.get("temp_unit")
            if not temp_unit:
                country = self.country_entry.get().strip() if self.country_entry else "US"
                temp_unit = "°F" if country.upper() == "US" else "°C"
            
            # Display temperature 
            if self.temp_label:
                self.temp_label.config(text=f"{temp:.0f}{temp_unit}")
            if self.city_label:
                self.city_label.config(text=f"{weather_data.get('city', 'Unknown')}")
            if self.desc_label:
                self.desc_label.config(text=weather_data.get('weather_detail', '').title())
            
            # Update summary 
            humidity = weather_data.get("humidity", "N/A")
            wind_speed = weather_data.get("wind_speed", "N/A")
            summary = (
                f"It's currently {temp:.0f}{temp_unit} in {weather_data.get('city', 'your area')}, "
                f"with {weather_data.get('weather_detail', '').lower()} conditions. "
                f"Humidity: {humidity}%, Wind Speed: {wind_speed} km/h."
            )
        
            if self.summary_label:
                self.summary_label.config(text=summary)
        
            weather_main = weather_data.get("weather_summary", "Clear")
            icon_path = get_icon_path(weather_main)
            emoji = WeatherEmoji.get_weather_emoji(weather_main)
            
            if self.icon_label:
                try:
                    img = Image.open(icon_path).resize((80, 80))
                    photo = ImageTk.PhotoImage(img)
                    self.icon_label.config(image=photo, text="")
                    self.icon_label.image = photo  # type: ignore
                except Exception as e:
                    # Fallback to emoji
                    self.icon_label.config(text=emoji, image="")                
        
            self.update_weather_details(weather_data)
                
        except Exception as e:
            self.logger.error(f"Error displaying weather: {e}")

    def _create_hourly_item(self, hour_data: dict, index: int, units: str = "metric"):
        """Create a single hourly forecast item"""
        try:
            if not self.widgets.get('hourly_scroll_frame'):
                return
                
            # Create hourly item frame
            item_frame = tk.Frame(self.widgets['hourly_scroll_frame'], bg="#374151", relief="raised", bd=1)
            item_frame.grid(row=0, column=index, padx=2, pady=5, sticky="nsew")
            
            # Get time from dt_txt or dt
            if 'dt_txt' in hour_data:
                time_str = hour_data['dt_txt']
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            elif 'dt' in hour_data:
                dt = datetime.fromtimestamp(hour_data['dt'])
            else:
                dt = datetime.now()
            
            # Display time
            time_label = tk.Label(item_frame, text=dt.strftime("%H:%M"), 
                                bg="#374151", fg="white", font=("Segoe UI", 10))
            time_label.pack(pady=2)
            
            # Weather icon
            weather_main = hour_data.get("weather", [{}])[0].get("main", "Clear")
            emoji = WeatherEmoji.get_weather_emoji(weather_main)
            icon_label = tk.Label(item_frame, text=emoji, bg="#374151", 
                                font=("Segoe UI", 16))
            icon_label.pack(pady=2)
            
            # Temperature
            temp = hour_data.get("main", {}).get("temp", 0)
            unit = "°F" if units == "imperial" else "°C"
            temp_label = tk.Label(item_frame, text=f"{temp:.0f}{unit}", 
                                bg="#374151", fg="white", font=("Segoe UI", 12, "bold"))
            temp_label.pack(pady=2)
            
        except Exception as e:
            self.logger.error(f"Error creating hourly item {index}: {e}")
            
    def display_hourly_forecast(self, hourly_data, units="metric"):
        """Updates the hourly forecast display"""
        # self.components.clear_widget('hourly_scroll_frame')
        
        if not hourly_data:
            return
            
        # Get forecast list from API response
        forecast_list = hourly_data.get("list", []) if isinstance(hourly_data, dict) else hourly_data
        
        # Display first 12 hours
        for i, hour_data in enumerate(forecast_list[:12]):
            try:
                self._create_hourly_item(hour_data, i, units)
            except Exception as e:
                self.logger.error(f"Error displaying hour {i}: {e}")

    def update_weather_details(self, weather_data):
        if not self.details_frame:
            return
            
        # Clear existing details with proper error handling
        try:
            children = self.details_frame.winfo_children()
            for widget in children:
                widget.destroy()
        except (AttributeError, tk.TclError):
            # Handle case where details_frame is None or destroyed
            return
                
        details = []
        
        # Determine temperature 
        country = self.country_entry.get().strip() if self.country_entry else "US"
        temp_unit = "°F" if country.upper() == "US" else "°C"
        
        if 'feels_like' in weather_data:
            feels_like = weather_data['feels_like']
            details.append(f"Feels like: {feels_like:.0f}{temp_unit}")
        
        # Display details
        for i, detail in enumerate(details):
            detail_label = tk.Label(self.details_frame, text=detail,
                                bg="#1e40af", fg="#9ca3af",
                                font=("Segoe UI", 10))
            detail_label.grid(row=0, column=i, padx=10, sticky="w")

    def display_forecast(self, forecast_list, units="metric"):
        # Check if forecast_items_frame exists
        if not self.forecast_items_frame:
            return
            
        # Clear existing widgets safely
        try:
            for widget in self.forecast_items_frame.winfo_children():
                widget.destroy()
        except (AttributeError, tk.TclError):
            # Handle case where forecast_items_frame is None or destroyed
            return
        
        for i in range(5):
            if self.forecast_items_frame: 
                self.forecast_items_frame.grid_columnconfigure(i, weight=1, uniform="forecast")
        today = datetime.now()
        for i, forecast in enumerate(forecast_list):
            try:
                day = today + timedelta(days=i)
                day_name = "Today" if i == 0 else day.strftime("%A")[:3]
                
                # Forecast item
                item_frame = tk.Frame(self.forecast_items_frame, bg="#4b5563", relief="raised", bd=1)
                item_frame.grid(row=0, column=i, padx=3, pady=5, sticky="nsew", ipady=15, ipadx=10)
                
               
                tk.Label(item_frame, text=day_name, bg="#4b5563", fg="white",
                        font=("Segoe UI", 12, "bold")).pack(pady=(5, 8))
                
                # Weather icon 
                weather_main = forecast.get("weather", [{}])[0].get("main", "")
                icon_path = get_icon_path(weather_main)
                
                try:               
                    img = Image.open(icon_path).resize((50, 50))  
                    photo = ImageTk.PhotoImage(img)
                    icon_label = tk.Label(item_frame, image=photo, bg="#4b5563")
                    icon_label.image = photo  # type: ignore
                    icon_label.pack(pady=5)
                except Exception as icon_error:
                    emoji = WeatherEmoji.get_weather_emoji(weather_main)
                    tk.Label(item_frame, text=emoji, bg="#4b5563", 
                            font=("Segoe UI", 24)).pack(pady=5)
                
                # Weather description 
                weather_desc = forecast.get("weather", [{}])[0].get("description", "").title()
                if weather_desc:
                    desc_label = tk.Label(item_frame, text=weather_desc, bg="#4b5563", fg="#d1d5db",
                                        font=("Segoe UI", 8), wraplength=80)
                    desc_label.pack(pady=(0, 5))
                
                # Temperature 
                temp_main = forecast.get('main', {})
                temp_max = temp_main.get('temp_max', 0)
                temp_min = temp_main.get('temp_min', 0)               
            
                unit = "°F" if units == "imperial" else "°C"
                
                # High temperature 
                high_temp_label = tk.Label(item_frame, 
                                    text=f"{temp_max:.0f}{unit}",
                                    bg="#4b5563", fg="white", 
                                    font=("Segoe UI", 14, "bold"))
                high_temp_label.pack()
                
                # Low temperature 
                low_temp_label = tk.Label(item_frame, 
                                    text=f"{temp_min:.0f}{unit}",
                                    bg="#4b5563", fg="#9ca3af", 
                                    font=("Segoe UI", 11))
                low_temp_label.pack(pady=(0, 8))
                
            except Exception as e:
                self.logger.error(f"Forecast display error for day {i}: {e}")
                # Create error card
                error_frame = tk.Frame(self.forecast_items_frame, bg="#ef4444")
                error_frame.grid(row=0, column=i, padx=3, pady=5, sticky="nsew")
                tk.Label(error_frame, text="Error", bg="#ef4444", fg="white",
                        font=("Segoe UI", 10)).pack(expand=True)
                
    # def refresh_all_panels(self) -> None:
    #     """Refresh all panels that support it"""
    #     try:
    #         # Check graphs panel
    #         if self.graphs_panel is not None:
    #             if hasattr(self.graphs_panel, 'refresh') and callable(getattr(self.graphs_panel, 'refresh')):
    #                 self.graphs_panel.refresh()
    #             else:
    #                 self.logger.debug("GraphsAndChartsPanel does not have a refresh method")
            
    #         # Check trends panel
    #         if self.trends_panel is not None:
    #             if hasattr(self.trends_panel, 'refresh') and callable(getattr(self.trends_panel, 'refresh')):
    #                 self.trends_panel.refresh()
    #             else:
    #                 self.logger.debug("TrendPanel does not have a refresh method")
            
    #         # Check stats panel
    #         if self.stats_panel is not None:
    #             if hasattr(self.stats_panel, 'refresh') and callable(getattr(self.stats_panel, 'refresh')):
    #                 self.stats_panel.refresh()
    #             else:
    #                 self.logger.debug("SimpleStatsPanel does not have a refresh method")
    #         else:
    #             # If no stats panel, refresh manual stats display
    #             self.show_statistics()
            
    #         # Check favorites panel
    #         if self.favorites_panel is not None:
    #             if hasattr(self.favorites_panel, 'refresh') and callable(getattr(self.favorites_panel, 'refresh')):
    #                 self.favorites_panel.refresh()
    #             else:
    #                 self.logger.debug("FavoriteCityPanel does not have a refresh method")
                    
    #     except Exception as e:
    #         self.logger.error(f"Error refreshing panels: {e}")
