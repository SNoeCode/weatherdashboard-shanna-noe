from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
from dotenv import load_dotenv
from config import Config
from config import setup_logger
from typing import cast, Optional
from features.simple_statisitics import get_weather_stats, show_statistics
from utils.date_time import format_local_time
from features.weather_icons import display_weather_with_icon, get_icon_path
import requests
from weather_data_fetcher import WeatherDataFetcher
from features.city_comparisons import CityComparisonPanel
from features.favorites_manager import FavoriteCityPanel
from features.weather_journal import save_journal_entry
from features.temp_graph_widget import render_temperature_graph, TemperatureGraphWidget
from features.theme_switcher import ThemeManager
from features.activity_suggester import suggest_activity
from features.tomorrows_guess import TomorrowGuessPanel
from features.weather_journal import JournalPanel
from features.trends import TrendPanel
from utils.date_time import format_local_time
load_dotenv()
cfg = Config.load_from_env()

# Simple icon mapping - moved complex icon logic to features/weather_icons.py
icon_map = {
    "Clear": "☀️",
    "Rain": "🌧️", 
    "Thunderstorm": "⛈️",
    "Clouds": "☁️",
    "Snow": "❄️",
    "Wind": "💨",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️"
}

class WeatherAppGUI:
    def __init__(self, fetcher, db, tracker, logger):
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger

        # Create main window
        self.root = tk.Tk()
        self.root.title("🌤️ Weather Dashboard Pro")  
        self.root.geometry("1400x900")
        self.root.configure(bg="#f8fafc")

        # Initialize theme manager
        self.theme_manager = ThemeManager(self.root)
        self.themed_widgets = []

        # Create main container
        self.main_container = tk.Frame(self.root, bg="#f8fafc")
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)

        self.current_weather_data = None
        
        # Setup UI components
        self.create_header()
        self.create_tab_navigation()
        self.create_content_area()
        
        # Initialize content sections
        self.setup_weather_overview()
        self.setup_graphs_section()
        self.setup_statistics_section()
        
        # Show weather overview by default
        self.show_section("weather")
                
        # Auto-load Knoxville weather on startup
        self.root.after(500, self.get_weather_threaded)
    
    def register_themed_widget(self, widget, bg_key=None, fg_key=None):
        """Register widgets for theme updates - actual theme logic in features/theme_switcher.py"""
        self.themed_widgets.append({
            'widget': widget,
            'bg_key': bg_key,
            'fg_key': fg_key
        })
        
    def get_weather_emoji(self, weather_main: str) -> str:
        """Get emoji representation for weather condition"""
        emoji_map = {
            "Clear": "☀️",
            "Rain": "🌧️", 
            "Thunderstorm": "⛈️",
            "Clouds": "☁️",
            "Snow": "❄️",
            "Wind": "💨",
            "Mist": "🌫️",
            "Fog": "🌫️",
            "Haze": "🌫️",
            "Dust": "🌪️",
            "Sand": "🌪️",
            "Ash": "🌋",
            "Squall": "💨",
            "Tornado": "🌪️"
        }
        return emoji_map.get(weather_main, "❓")

    def create_header(self):
        """Create header with time and search controls"""
        header_frame = tk.Frame(self.main_container, bg="#2563eb", height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Current time
        current_time = datetime.now().strftime("%I:%M %p")
        self.time_label = tk.Label(header_frame, text=current_time, 
                                  font=("Segoe UI", 24, "bold"),
                                  bg="#2563eb", fg="white")
        self.time_label.pack(side='left', anchor='w', padx=20, pady=15)
        
        # Search controls
        search_frame = tk.Frame(header_frame, bg="#2563eb")
        search_frame.pack(side='right', anchor='e', padx=20, pady=15)
        
        self.city_entry = tk.Entry(search_frame, width=15, 
                                  font=("Segoe UI", 10), bd=1)
        self.city_entry.pack(side='left', padx=(0, 5))
        self.city_entry.insert(0, "Knoxville")
        
        self.country_entry = tk.Entry(search_frame, width=5, 
                                     font=("Segoe UI", 10), bd=1)
        self.country_entry.pack(side='left', padx=(0, 10))
        self.country_entry.insert(0, "US")
        
        search_button = tk.Button(search_frame, text="🔍", 
                                 font=("Segoe UI", 12), bd=1, cursor="hand2",
                                 bg="#1d4ed8", fg="white",
                                 command=self.get_weather_threaded)
        search_button.pack(side='left', padx=2)
        
        theme_button = tk.Button(search_frame, text="🌙", 
                                font=("Segoe UI", 12), bd=1, cursor="hand2",
                                bg="#1d4ed8", fg="white",
                                command=self.toggle_theme)
        theme_button.pack(side='left', padx=2)
        
        activity_button = tk.Button(search_frame, text="🎯", 
                                   font=("Segoe UI", 12), bd=1, cursor="hand2",
                                   bg="#1d4ed8", fg="white",
                                   command=self.show_activity_suggestion)
        activity_button.pack(side='left', padx=2)
        
        # Location display
        self.location_label = tk.Label(header_frame, text="Loading...", 
                                      font=("Segoe UI", 10), justify='right',
                                      bg="#2563eb", fg="#cbd5e1")
        self.location_label.pack(side='bottom', anchor='e', padx=20)
        
        # Update time every minute
        self.update_time()

    def create_tab_navigation(self):
        """Create top tab navigation with all main sections"""
        self.tab_frame = tk.Frame(self.main_container, bg="#f8fafc", height=60)
        self.tab_frame.pack(fill='x')
        self.tab_frame.pack_propagate(False)
        
        # Updated tab buttons - moved favorites, journal, etc. to top level
        self.tab_buttons = {}
        tabs = [
            ("weather", "🌤️ Weather Overview"),
            ("graphs", "📊 Charts & Graphs"), 
            ("stats", "📈 Statistics & Data"),
            ("favorites", "⭐ Favorites"),
            ("journal", "📓 Journal"),
            ("guess", "🔮 Tomorrow's Guess"),
            ("compare", "🏙️ Compare Cities")
        ]
        
        for tab_id, tab_name in tabs:
            btn = tk.Button(self.tab_frame, text=tab_name,
                        font=("Segoe UI", 10, "bold"),
                        bg="#e2e8f0", fg="#475569",
                        bd=0, cursor="hand2",
                        padx=20, pady=15,
                        relief="flat",
                        command=lambda t=tab_id: self.show_section(t))
            btn.pack(side='left', padx=2, pady=10)
            self.tab_buttons[tab_id] = btn
        
    def create_content_area(self):
        """Create main content area and initialize all sections"""
        self.content_area = tk.Frame(self.main_container, bg="#f8fafc")
        self.content_area.pack(fill='both', expand=True)
        
        # Create sections dictionary
        self.sections = {}
        
        # Initialize all sections immediately
        self.setup_weather_overview()
        self.setup_graphs_section() 
        self.setup_statistics_section()
        self.setup_favorites_section()
        self.setup_journal_section()
        self.setup_guess_section()
        self.setup_compare_section()

    # def setup_favorites_section(self):
    #     """Setup favorites section as top-level tab"""
    #     favorites_section = tk.Frame(self.content_area, bg="#f8fafc")
    #     self.sections["favorites"] = favorites_section
        
    #     # Title
    #     title_label = tk.Label(favorites_section, text="⭐ Favorite Cities Dashboard",
    #                         font=("Segoe UI", 20, "bold"),
    #                         bg="#f8fafc", fg="#1f2937")
    #     title_label.pack(pady=20)
        
    #     try:
    #         # Initialize favorites panel
    #         self.favorites_panel = FavoriteCityPanel(favorites_section, self.tracker, self.db, self.logger, cfg)
    #     except Exception as e:
    #         self.logger.error(f"Error initializing favorites panel: {e}")
    #         error_label = tk.Label(favorites_section, text=f"Error loading favorites: {str(e)}",
    #                             bg="#f8fafc", fg="red")
    #         error_label.pack(expand=True)



        
    def show_section(self, section_id):
        """Show specific section and update tab styling"""
        # Hide all sections
        for section in self.sections.values():
            section.pack_forget()
            
        # Show selected section
        if section_id in self.sections:
            self.sections[section_id].pack(fill='both', expand=True, padx=20, pady=20)
        
        # Update tab button styles
        for tab_id, btn in self.tab_buttons.items():
            if tab_id == section_id:
                btn.config(bg="#2563eb", fg="white")
            else:
                btn.config(bg="#e2e8f0", fg="#475569")


    def setup_weather_overview(self):
        """Setup weather overview section - simplified without sub-tabs"""
        weather_section = tk.Frame(self.content_area, bg="#f8fafc")
        self.sections["weather"] = weather_section
        
        # Main weather display
        main_weather_frame = tk.Frame(weather_section, bg="#1e40af", height=300)
        main_weather_frame.pack(fill='x', pady=(0, 20))
        main_weather_frame.pack_propagate(False)
        
        # Left side - Temperature and basic info
        left_frame = tk.Frame(main_weather_frame, bg="#1e40af")
        left_frame.pack(side='left', fill='y', padx=20, pady=20)
        
        # Temperature display
        self.temp_label = tk.Label(left_frame, text="--°", 
                                font=("Segoe UI", 72, "bold"),
                                bg="#1e40af", fg="white")
        self.temp_label.pack(anchor='w')
        
        # City name
        self.city_label = tk.Label(left_frame, text="Loading...", 
                                font=("Segoe UI", 18),
                                bg="#1e40af", fg="white")
        self.city_label.pack(anchor='w', pady=(10, 0))
        
        # Weather description
        self.desc_label = tk.Label(left_frame, text="", 
                                font=("Segoe UI", 12),
                                bg="#1e40af", fg="#cbd5e1")
        self.desc_label.pack(anchor='w')
        
        # Right side - Weather icon and details
        right_frame = tk.Frame(main_weather_frame, bg="#1e40af")
        right_frame.pack(side='right', fill='y', padx=20, pady=20)
        
        # Weather icon/emoji
        self.icon_label = tk.Label(right_frame, text="", font=("Segoe UI", 48),
                                bg="#1e40af", fg="white")
        self.icon_label.pack(anchor='e', pady=(0, 20))
        
        # Detailed weather info
        self.details_frame = tk.Frame(right_frame, bg="#1e40af")
        self.details_frame.pack(anchor='e')
        
        # Forecast section
        self.create_forecast_section(weather_section)
        
        # Additional weather info section
        self.create_additional_weather_info(weather_section)


    def create_forecast_section(self, parent):
        """Create forecast section within weather overview"""
        self.forecast_container = tk.Frame(parent, bg="#374151")
        self.forecast_container.pack(fill='x', pady=(0, 20))
        self.forecast_container.pack_propagate(True)

        header = tk.Label(self.forecast_container, text="5-Day Forecast",
                        font=("Segoe UI", 12, "bold"),
                        bg="#374151", fg="white")
        header.pack(pady=(8, 4))

        self.forecast_items_frame = tk.Frame(self.forecast_container, bg="#374151")
        self.forecast_items_frame.pack(fill='x', padx=10)
    
    def create_additional_weather_tabs(self, parent):
        """Create sub-tabs for weather features"""
        sub_tab_frame = tk.Frame(parent, bg="#f8fafc")
        sub_tab_frame.pack(fill='both', expand=True)
        
        # Create notebook for weather sub-features
        self.weather_notebook = ttk.Notebook(sub_tab_frame)
        self.weather_notebook.pack(fill='both', expand=True)
        
        # Create tab frames
        self.favorites_tab = ttk.Frame(self.weather_notebook)
        self.journal_tab = ttk.Frame(self.weather_notebook)
        self.guess_tab = ttk.Frame(self.weather_notebook)
        self.compare_tab = ttk.Frame(self.weather_notebook)
        
        self.weather_notebook.add(self.favorites_tab, text="⭐ Favorites")
        self.weather_notebook.add(self.journal_tab, text="📓 Journal")
        self.weather_notebook.add(self.guess_tab, text="🔮 Tomorrow's Guess")
        self.weather_notebook.add(self.compare_tab, text="🏙️ Compare Cities")
        
        # Initialize feature panels
        try:
            self.favorites_panel = FavoriteCityPanel(self.favorites_tab, self.tracker, self.db, self.logger, cfg)
            self.compare_panel = CityComparisonPanel(self.compare_tab, self.db, self.fetcher, self.logger)
            self.journal_panel = JournalPanel(self.journal_tab, self.db, self.logger, cfg)  
            self.guess_panel = TomorrowGuessPanel(self.guess_tab, self.fetcher, self.logger, cfg)
        except Exception as e:
            self.logger.error(f"Error initializing panels: {e}")
            
            
    def setup_graphs_section(self):
        """Setup graphs and charts section - direct display"""
        graphs_section = tk.Frame(self.content_area, bg="#f8fafc")
        self.sections["graphs"] = graphs_section
        
        # Controls at top
        controls_frame = tk.Frame(graphs_section, bg="#f8fafc", height=80)
        controls_frame.pack(fill='x', pady=(0, 10))
        controls_frame.pack_propagate(False)
        
        # Title and controls in same row
        title_label = tk.Label(controls_frame, text="📊 Weather Charts & Graphs",
                            font=("Segoe UI", 20, "bold"),
                            bg="#f8fafc", fg="#1f2937")
        title_label.pack(side='left', padx=20, pady=20)
        
        # Control buttons on right
        button_frame = tk.Frame(controls_frame, bg="#f8fafc")
        button_frame.pack(side='right', padx=20, pady=20)
        
        temp_graph_btn = tk.Button(button_frame, text="📈 Temperature",
                                font=("Segoe UI", 11, "bold"),
                                bg="#10b981", fg="white",
                                padx=15, pady=8,
                                cursor="hand2",
                                command=self.show_temperature_graph)
        temp_graph_btn.pack(side='left', padx=(0, 5))
        
        trends_btn = tk.Button(button_frame, text="📊 Trends",
                            font=("Segoe UI", 11, "bold"),
                            bg="#3b82f6", fg="white",
                            padx=15, pady=8,
                            cursor="hand2",
                            command=self.show_trends_panel)
        trends_btn.pack(side='left')
        
        # Graph display area - full size
        self.graph_display_frame = tk.Frame(graphs_section, bg="white", relief="solid", bd=1)
        self.graph_display_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Initialize with temperature graph by default
        self.root.after(100, self.show_temperature_graph)    
        

    
    def setup_statistics_section(self):
        """Setup statistics and data section"""
        stats_section = tk.Frame(self.content_area, bg="#f8fafc")
        self.sections["stats"] = stats_section
        
        # Title
        title_label = tk.Label(stats_section, text="📈 Weather Statistics & Data",
                              font=("Segoe UI", 20, "bold"),
                              bg="#f8fafc", fg="#1f2937")
        title_label.pack(pady=(0, 20))
        
        # Stats controls
        controls_frame = tk.Frame(stats_section, bg="#f8fafc")
        controls_frame.pack(fill='x', pady=(0, 20))
        
        refresh_btn = tk.Button(controls_frame, text="🔄 Refresh Stats",
                               font=("Segoe UI", 12, "bold"),
                               bg="#3b82f6", fg="white",
                               padx=20, pady=10,
                               cursor="hand2",
                               command=self.show_simple_statistics)
        refresh_btn.pack(side='left', padx=(0, 10))
        
        export_btn = tk.Button(controls_frame, text="💾 Export Data",
                              font=("Segoe UI", 12, "bold"),
                              bg="#f59e0b", fg="white",
                              padx=20, pady=10,
                              cursor="hand2",
                              command=self.save_to_csv)
        export_btn.pack(side='left')
        
        # Stats display area
        self.stats_display_frame = tk.Frame(stats_section, bg="white", relief="solid", bd=1)
        self.stats_display_frame.pack(fill='both', expand=True)
        
        # Data summary
        self.data_summary_label = tk.Label(self.stats_display_frame,
                                          text="Loading data summary...",
                                          font=("Segoe UI", 12),
                                          bg="white", fg="#374151",
                                          justify='left')
        self.data_summary_label.pack(padx=20, pady=20, anchor='w')
        
        self.update_data_summary()
    
    def show_trends_panel(self):
        """Show trends panel in graphs section"""
        try:
            # Clear graph display
            for widget in self.graph_display_frame.winfo_children():
                widget.destroy()
            
            # Initialize trends panel
            self.trends_panel = TrendPanel(self.graph_display_frame, self.db, self.logger, cfg)
        except Exception as e:
            self.logger.error(f"Error showing trends panel: {e}")
            error_label = tk.Label(self.graph_display_frame,
                                 text=f"Error loading trends: {str(e)}",
                                 bg="white", fg="red")
            error_label.pack(expand=True)
    
    def toggle_theme(self):
        """Toggle theme - actual logic in features/theme_switcher.py"""
        try:
            new_theme = self.theme_manager.toggle_theme()
            self.logger.info(f"Theme switched to: {new_theme}")
        except Exception as e:
            self.logger.error(f"Theme toggle error: {e}")
    
    def show_activity_suggestion(self):
        """Show activity suggestion - logic in features/activity_suggester.py"""
        if self.current_weather_data:
            try:
                weather_condition = self.current_weather_data.get('weather_summary', 'Clear')
                activity = suggest_activity(self.current_weather_data, weather_condition)
                messagebox.showinfo("Activity Suggestion", 
                                f"Based on current weather in {self.current_weather_data['city']}:\n\n"
                                f"🎯 Suggested Activity: {activity}")
            except Exception as e:
                self.logger.error(f"Error getting activity suggestion: {e}")
                messagebox.showinfo("Activity Suggestion", "Unable to get activity suggestion at this time.")
        else:
            messagebox.showinfo("Activity Suggestion", "Please search for weather first!")
    
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%I:%M %p")
        if hasattr(self, 'time_label'):
            self.time_label.config(text=current_time)
        self.root.after(60000, self.update_time)
    
    def update_weather_details(self, weather_data, unit):
        """Update weather details"""
        # Clear existing details
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        details = []
        
        # Feels like temperature
        if 'feels_like' in weather_data:
            feels_like = weather_data['feels_like']
            if weather_data.get("country") == "US":
                feels_like = (feels_like * 9 / 5) + 32
            details.append(f"Feels like: {feels_like:.0f}{unit}")
        
        # Other details
        if 'humidity' in weather_data:
            details.append(f"Humidity: {weather_data['humidity']}%")
        
        if 'pressure' in weather_data:
            details.append(f"Pressure: {weather_data['pressure']} hPa")
        
        if 'wind_speed' in weather_data:
            details.append(f"Wind: {weather_data['wind_speed']} m/s")
        
        # Display details
        for detail in details:
            detail_label = tk.Label(self.details_frame, text=detail, bg="#1e40af", 
                                fg="#9ca3af", font=("Segoe UI", 10))
            detail_label.pack(anchor='e', pady=2)

    def display_main_weather(self, weather_data):
        """Display main weather info"""
        try:
            # Temperature conversion
            temp = weather_data["temp"]
            if weather_data.get("country") == "US":
                temp = (temp * 9 / 5) + 32
                unit = "°F"
            else:
                unit = "°C"
            
            # Update main display
            self.temp_label.config(text=f"{temp:.0f}°")
            self.city_label.config(text=f"{weather_data.get('city', 'Unknown')}")
            self.desc_label.config(text=weather_data.get('weather_detail', '').capitalize())
            
            # Display weather icon/emoji
            weather_main = weather_data.get("weather_summary", "Clear")
            
            # Try to use actual icon first (from features/weather_icons.py)
            try:
                icon_path = get_icon_path(weather_main)
                if os.path.exists(icon_path):
                    img = Image.open(icon_path).resize((80, 80))
                    photo = ImageTk.PhotoImage(img)
                    self.icon_label.config(image=photo, text="")
                    self.icon_label.image = photo #type: ignore
                else:
                    raise FileNotFoundError("Icon not found")
            except:
                # Fallback to emoji
                emoji = icon_map.get(weather_main, "❓")
                self.icon_label.config(text=emoji, font=("Segoe UI", 48))
            
            # Update detailed info
            self.update_weather_details(weather_data, unit)
            
        except Exception as e:
            self.logger.error(f"Error displaying weather: {e}")
    
    def get_weather_threaded(self):
        """Start weather fetch in background thread"""
        threading.Thread(target=self.get_weather, daemon=True).start()

    def get_weather(self):
        city = self.city_entry.get().strip() or "Knoxville"
        country = self.country_entry.get().strip() or "US"

        try:
            self.root.after(0, lambda: self.temp_label.config(text="Loading..."))
            self.root.after(0, lambda: self.city_label.config(text=f"{city}, {country}"))

            current_result = self.fetcher.fetch_current_weather(city, country)
            if current_result:
                self.current_weather_data = current_result
                self.db.insert_reading(current_result)
                self.tracker.database.log_request("manual_search", None, "success")
                self.root.after(0, lambda: self.display_main_weather(current_result))

                forecast_result = self.fetcher.fetch_five_day_forecast(city, country)
                forecast_list = forecast_result.get("list", []) if forecast_result else []

                if forecast_list:
                    daily_forecasts = forecast_list[::8][:5]
                    self.root.after(0, lambda: self.render_forecast_cards(daily_forecasts, country))
                else:
                    self.logger.warning(f"No forecast list found for {city}")
                    self.root.after(0, lambda: messagebox.showwarning("Forecast Unavailable", f"No forecast data for {city}."))

                self.root.after(0, lambda: self.location_label.config(text=f"{city}, {country}\nOnline"))
                self.root.after(100, self.show_simple_statistics)
            else:
                self.root.after(0, lambda: messagebox.showerror("Weather Error", "Could not fetch weather data."))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Weather fetch failed: {e}"))

    def render_forecast_cards(self, forecast_list, country):
        self.logger.info(f"Rendering forecast: {len(forecast_list)} entries")

        # Clear previous forecast items
        for widget in self.forecast_items_frame.winfo_children():
            widget.destroy()

        if not forecast_list:
            tk.Label(self.forecast_items_frame, text="⚠️ No forecast available", font=("Segoe UI", 12),
                    bg="#374151", fg="white").pack()
            return

        today = datetime.now()
        for i, forecast in enumerate(forecast_list):
            try:
                day = today + timedelta(days=i)
                day_name = "Today" if i == 0 else day.strftime("%A")[:3].upper()

                item_frame = tk.Frame(self.forecast_items_frame, bg="#374151", width=100, height=110)
                item_frame.pack(side='left', padx=6, pady=5)
                item_frame.pack_propagate(False)

                tk.Label(item_frame, text=day_name, bg="#374151", fg="white",
                        font=("Segoe UI", 9, "bold")).pack()

                weather_main = forecast.get("weather", [{}])[0].get("main", "")
                icon_path = get_icon_path(weather_main)

                if os.path.exists(icon_path):
                    img = Image.open(icon_path).resize((28, 28))
                    photo = ImageTk.PhotoImage(img)
                    icon_label = tk.Label(item_frame, image=photo, bg="#374151")
                    icon_label.image = photo # type: ignore
                    icon_label.pack(pady=3)
                else:
                    emoji = self.get_weather_emoji(weather_main)
                    tk.Label(item_frame, text=emoji, bg="#374151", font=("Segoe UI", 14)).pack(pady=3)

                temp_main = forecast.get('main', {})
                temp_max = temp_main.get('temp_max')
                temp_min = temp_main.get('temp_min')

                if temp_max is None or temp_min is None:
                    raise ValueError("Missing temperature data")

                if country == "US":
                    temp_max = (temp_max * 9/5) + 32
                    temp_min = (temp_min * 9/5) + 32

                tk.Label(item_frame, text=f"{temp_max:.0f}°/{temp_min:.0f}°",
                        bg="#374151", fg="#9ca3af", font=("Segoe UI", 8)).pack()

            except Exception as e:
                self.logger.error(f"Forecast render error at index {i}: {e}")
                tk.Label(self.forecast_items_frame, text=f"⚠️ Error rendering forecast for day {i + 1}",
                        bg="#374151", fg="red", font=("Segoe UI", 10)).pack()
    
    def show_simple_statistics(self):
        """Show basic statistics - complex logic moved to features/simple_statistics.py"""
        try:
            city = self.city_entry.get().strip() or "Knoxville"
            country = self.country_entry.get().strip() or "US"
            
            # Clear existing stats
            for widget in self.stats_display_frame.winfo_children():
                widget.destroy()
                
            # Recreate data summary label
            self.data_summary_label = tk.Label(self.stats_display_frame,
                                              text="Loading statistics...",
                                              font=("Segoe UI", 12),
                                              bg="white", fg="#374151",
                                              justify='left')
            self.data_summary_label.pack(padx=20, pady=20, anchor='w')
            
            # Get recent readings
            readings = self.db.fetch_recent(city, country, hours=168)  # 1 week
            
            if not readings:
                self.data_summary_label.config(text="No weather data available for statistics")
                return
            
            # Use statistics feature
            stats_text = get_weather_stats(city, country)
            self.data_summary_label.config(text=f"📊 Statistics for {city}, {country}:\n\n{stats_text}")
            
        except Exception as e:
            self.logger.error(f"Error showing statistics: {e}")
            if hasattr(self, 'data_summary_label'):
                self.data_summary_label.config(text=f"Error loading statistics: {str(e)}")
    
    def show_temperature_graph(self):
        """Show temperature graph - logic moved to features/temp_graph_widget.py"""
        try:
            city = self.city_entry.get().strip() or "Knoxville"
            country = self.country_entry.get().strip() or "US"
            
            # Clear graph display
            for widget in self.graph_display_frame.winfo_children():
                widget.destroy()
            
            # Get recent readings for the graph
            readings = self.db.fetch_recent(city, country, hours=72)  # 3 days
            
            if readings:
                # Create temperature graph widget in the graph display frame
                try:
                    graph_widget = TemperatureGraphWidget(self.graph_display_frame, readings)
                    # Don't try to access .pack or .widget - just let the widget handle itself
                    # TemperatureGraphWidget likely creates its own widgets internally
                except Exception as graph_error:
                    self.logger.error(f"TemperatureGraphWidget error: {graph_error}")
                    # Fallback to simple render function if widget fails
                    render_temperature_graph(self.graph_display_frame, readings, timezone_str=cfg.default_timezone)

            else:
                # Show no data message
                no_data_label = tk.Label(self.graph_display_frame,
                                       text=f"📈 No temperature data available for {city}, {country}\n\nTry searching for weather data first!",
                                       font=("Segoe UI", 14),
                                       bg="white", fg="#6b7280")
                no_data_label.pack(expand=True)
                
        except Exception as e:
            self.logger.error(f"Graph error: {e}")
            # Show error in the graph display frame
            error_label = tk.Label(self.graph_display_frame,
                                 text=f"❌ Error generating temperature graph:\n{str(e)}",
                                 font=("Segoe UI", 12),
                                 bg="white", fg="red")
            error_label.pack(expand=True)

    def update_data_summary(self):
        """Simple data summary - complex logic moved to features/data_export.py"""
        try:
            all_readings = self.db.get_all_readings()
            
            summary_text = f"📊 Database Summary:\n\n"
            summary_text += f"• Total readings: {len(all_readings)}\n"
            
            if all_readings:
                latest_reading = all_readings[-1]
                summary_text += f"• Latest: {latest_reading.get('city', 'Unknown')}\n"
                summary_text += f"• Last updated: {latest_reading.get('timestamp', 'Unknown')}\n"
                
                # Add some basic stats
                cities = set(reading.get('city', '') for reading in all_readings[-10:])  # Last 10 readings
                summary_text += f"• Recent cities searched: {len(cities)}\n"
                
                if len(all_readings) > 1:
                    first_reading = all_readings[0]
                    summary_text += f"• First reading: {first_reading.get('timestamp', 'Unknown')}\n"
            else:
                summary_text += "• No weather data available yet\n"
                summary_text += "• Search for weather to start collecting data"
            
            if hasattr(self, 'data_summary_label'):
                self.data_summary_label.config(text=summary_text)
                
        except Exception as e:
            self.logger.error(f"Data summary error: {e}")
            if hasattr(self, 'data_summary_label'):
                self.data_summary_label.config(text=f"Error loading summary: {str(e)}")
                
                
    def setup_favorites_section(self):
        """Setup favorites section as top-level tab"""
        favorites_section = tk.Frame(self.content_area, bg="#f8fafc")
        self.sections["favorites"] = favorites_section
        
        # Title
        title_label = tk.Label(favorites_section, text="⭐ Favorite Cities Dashboard",
                            font=("Segoe UI", 20, "bold"),
                            bg="#f8fafc", fg="#1f2937")
        title_label.pack(pady=20)
        
        try:
            # Initialize favorites panel
            self.favorites_panel = FavoriteCityPanel(favorites_section, self.tracker, self.db, self.logger, cfg)
        except Exception as e:
            self.logger.error(f"Error initializing favorites panel: {e}")
            error_label = tk.Label(favorites_section, text=f"Error loading favorites: {str(e)}",
                                bg="#f8fafc", fg="red")
            error_label.pack(expand=True)

    def setup_journal_section(self):
        """Setup journal section as top-level tab"""
        journal_section = tk.Frame(self.content_area, bg="#f8fafc")
        self.sections["journal"] = journal_section
        
        # Title
        title_label = tk.Label(journal_section, text="📓 Weather Journal",
                            font=("Segoe UI", 20, "bold"),
                            bg="#f8fafc", fg="#1f2937")
        title_label.pack(pady=20)
        
        try:
            # Initialize journal panel
            self.journal_panel = JournalPanel(journal_section, self.db, self.logger, cfg)
        except Exception as e:
            self.logger.error(f"Error initializing journal panel: {e}")
            error_label = tk.Label(journal_section, text=f"Error loading journal: {str(e)}",
                                bg="#f8fafc", fg="red")
            error_label.pack(expand=True)


    def setup_compare_section(self):
        """Setup city comparison section as top-level tab"""
        compare_section = tk.Frame(self.content_area, bg="#f8fafc")
        self.sections["compare"] = compare_section
        
        # Title
        title_label = tk.Label(compare_section, text="🏙️ Compare Cities",
                            font=("Segoe UI", 20, "bold"),
                            bg="#f8fafc", fg="#1f2937")
        title_label.pack(pady=20)
        
        try:
            # Initialize comparison panel
            self.compare_panel = CityComparisonPanel(compare_section, self.db, self.fetcher, self.logger)
        except Exception as e:
            self.logger.error(f"Error initializing compare panel: {e}")
            error_label = tk.Label(compare_section, text=f"Error loading comparison: {str(e)}",
                                bg="#f8fafc", fg="red")
            error_label.pack(expand=True)
        
    def setup_guess_section(self):
        """Setup tomorrow's guess section as top-level tab"""
        guess_section = tk.Frame(self.content_area, bg="#f8fafc")
        self.sections["guess"] = guess_section
        
        # Title
        title_label = tk.Label(guess_section, text="🔮 Tomorrow's Weather Guess",
                            font=("Segoe UI", 20, "bold"),
                            bg="#f8fafc", fg="#1f2937")
        title_label.pack(pady=20)
        
        try:
            # Initialize guess panel
            self.guess_panel = TomorrowGuessPanel(guess_section, self.fetcher, self.logger, cfg)
        except Exception as e:
            self.logger.error(f"Error initializing guess panel: {e}")
            error_label = tk.Label(guess_section, text=f"Error loading guess panel: {str(e)}",
                                bg="#f8fafc", fg="red")
            error_label.pack(expand=True)

    def create_additional_weather_info(self, parent):
        """Create additional weather information section"""
        info_frame = tk.Frame(parent, bg="#f8fafc")
        info_frame.pack(fill='both', expand=True, pady=20)
        
        # Quick stats or hourly forecast could go here
        info_label = tk.Label(info_frame, text="Additional weather details will appear here",
                            font=("Segoe UI", 12),
                            bg="#f8fafc", fg="#6b7280")
        info_label.pack(expand=True)


    def save_to_csv(self):
        """Export to CSV - complex logic moved to features/data_export.py"""
        try:
            # Ask user where to save the file
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save weather data as..."
            )
            
            if not filename:
                return  # User cancelled
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Export the data
            success = self.db.export_readings_to_csv(filename)
            
            if success:
                messagebox.showinfo("✅ Export Successful", 
                                  f"Weather data exported to:\n{filename}")
            else:
                messagebox.showwarning("⚠️ Export Failed", 
                                     "No weather records available to export.")
                                     
        except Exception as e:
            self.logger.error(f"CSV export error: {e}")
            messagebox.showerror("Export Error", 
                               f"Failed to export data:\n{str(e)}")

    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.logger.info("Weather Dashboard application closing")

# Additional helper methods that might be missing:

    def refresh_current_section(self):
        """Refresh the currently visible section"""
        try:
            # Find which section is currently visible
            for section_id, section_frame in self.sections.items():
                if section_frame.winfo_viewable():
                    if section_id == "weather":
                        self.get_weather_threaded()
                    elif section_id == "graphs":
                        self.show_temperature_graph()
                    elif section_id == "stats":
                        self.show_simple_statistics()
                    break
        except Exception as e:
            self.logger.error(f"Error refreshing section: {e}")

    def on_closing(self):
        """Handle application closing"""
        try:
            self.logger.info("Closing Weather Dashboard...")
            self.root.destroy()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")







