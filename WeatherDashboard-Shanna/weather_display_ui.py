# from components.creater_header import CreateHeader
# from components.create_feature_tabs import CreateFeatureTabs
# from components.display_features_ui import DisplayFeatures
# from components.get_weather import GetWeather
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
from components.create_dashboard_layout_ui import CreateDashboardLayout
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
load_dotenv()
cfg = Config.load_from_env()
class WeatherAppGUI:
    def __init__(self, fetcher, db, tracker, logger, cfg):
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger
        self.cfg = cfg
        self.current_weather_data = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("🌤️ Weather Dashboard Pro")
        self.root.geometry("1600x1000")
        self.root.configure(bg="#f8fafc")
        
        # Configure main grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(self.root)
        self.weather_graphs = WeatherGraphs(self.theme_manager)
        self.create_header()
        self.create_tab_interface()
        
        self.root.after(1000, self.get_weather_threaded)
        self.summary_label = ttk.Label(self.root, text="", font=("Segoe UI", 10), foreground="#334155")
        self.summary_label.grid(row=2, column=0, sticky="w", padx=20, pady=(10, 0))
        
        
        # self.header = CreateHeader(
        #     root=self.root,
        #     get_weather_callback=self.get_weather_threaded,
        #     toggle_theme_callback=self.toggle_theme
        # )
        # city, country = self.header.get_location()
        

        # self.display_features.display_current_weather(weather_data)
    
    
            # In your weather update method
        # self.display_features = DisplayFeatures(
        #     parent=self.root,
        #     theme_manager=self.theme_manager,
        #     db=self.db,
        #     logger=self.logger,
        #     fetcher=self.fetcher,
        #     cfg=self.cfg,
        #     city_entry=self.city_entry,
        #     country_entry=self.country_entry
        # )
        
        # self.display_features.set_ui_references(
        #     temp_label=self.widgets.get('temp_label'),
        #     city_label=self.widgets.get('city_label'),
        #     desc_label=self.widgets.get('desc_label'),
        #     icon_label=self.widgets.get('icon_label'),
        #     details_frame=self.widgets.get('details_frame'),
        #     forecast_items_frame=self.widgets.get('forecast_items_frame'),
        #     hourly_scroll_frame=self.widgets.get('hourly_scroll_frame'),
        #     graph_container=self.widgets.get('graph_container'),
        #     activity_content_frame=self.widgets.get('activity_content_frame')
        # )
    def create_header(self):       
        header_frame = tk.Frame(self.root, bg="#2563eb", height=80)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Current time (LEFT)
        current_time = datetime.now().strftime("%I:%M %p")
        self.time_label = tk.Label(header_frame, text=current_time, 
                                  font=("Segoe UI", 24, "bold"),
                                  bg="#2563eb", fg="white")
        self.time_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # App title (CENTER)
        title_label = tk.Label(header_frame, text="🌤️ Weather Dashboard Pro", 
                              font=("Segoe UI", 20, "bold"),
                              bg="#2563eb", fg="white")
        title_label.grid(row=0, column=1, pady=15)
        
        # Search controls (RIGHT)
        search_frame = tk.Frame(header_frame, bg="#2563eb")
        search_frame.grid(row=0, column=2, sticky="e", padx=20, pady=15)
        
        self.city_entry = tk.Entry(search_frame, width=15, font=("Segoe UI", 10))
        self.city_entry.grid(row=0, column=0, padx=(0, 5))
        self.city_entry.insert(0, "Knoxville")
        
        self.country_entry = tk.Entry(search_frame, width=5, font=("Segoe UI", 10))
        self.country_entry.grid(row=0, column=1, padx=(0, 10))
        self.country_entry.insert(0, "US")
        
        search_btn = tk.Button(search_frame, text="🔍", font=("Segoe UI", 12),
                              bg="#1d4ed8", fg="white", cursor="hand2",
                              command=self.get_weather_threaded)
        search_btn.grid(row=0, column=2, padx=2)
        
        theme_btn = tk.Button(search_frame, text="🌙", font=("Segoe UI", 12),
                             bg="#1d4ed8", fg="white", cursor="hand2",
                             command=self.toggle_theme)
        theme_btn.grid(row=0, column=3, padx=2)
        
        
        self.update_time()
    
    def create_tab_interface(self):     
        # Tab notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
                
        # Create all tabs
        self.create_dashboard_tab()
        self.create_graphs_tab()
        self.create_trends_tab()
        self.create_statistics_tab()
        self.create_favorites_tab()
        self.create_journal_tab()
        self.create_guess_tab()
        self.create_compare_tab()
        self.create_activity_tab()
    
    # def create_dashboard_tab(self):
    #     """Create main dashboard tab with new layout component"""
    #     dashboard_frame = ttk.Frame(self.notebook)
    #     self.notebook.add(dashboard_frame, text="🌤️ Dashboard")
        
    #     # Initialize the dashboard layout component
    #     self.dashboard_layout = CreateDashboardLayout(
    #     parent=dashboard_frame,
    #     theme_manager=self.theme_manager,
    #     db=self.db,
    #     logger=self.logger,
    #     fetcher=self.fetcher
    # )
        
    #     Create the dashboard layout
    #     self.dashboard_layout.create_dashboard_layout(dashboard_frame)
        
    
    def create_dashboard_tab(self):
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="🌤️ Dashboard")
        
        # Configure grid for 2x2 layout
        dashboard_frame.grid_rowconfigure(0, weight=1)
        dashboard_frame.grid_rowconfigure(1, weight=1)
        dashboard_frame.grid_columnconfigure(0, weight=1)
        dashboard_frame.grid_columnconfigure(1, weight=1)
        
        # Section 1: Current Weather (Top Left)
        self.create_current_weather_section(dashboard_frame)
        
        # Section 2: 5-Day Forecast (Top Right)
        self.create_forecast_section(dashboard_frame)
        
        # Section 3: Weather Map (Bottom Left)
        self.create_weather_map_section(dashboard_frame)
        
        # Section 4: Activity Tracker (Bottom Right)
        self.create_activity_tracker_section(dashboard_frame)
        
    def create_current_weather_section(self, parent):      
        weather_frame = tk.Frame(parent, bg="#1e40af", relief="solid", bd=2)
        weather_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        weather_frame.grid_columnconfigure(1, weight=1)
        
        header_label = tk.Label(weather_frame, text="🌡️ Current Weather", 
                               font=("Segoe UI", 16, "bold"),
                               bg="#1e40af", fg="white")
        header_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Temperature 
        self.temp_label = tk.Label(weather_frame, text="--°F", 
                                  font=("Segoe UI", 48, "bold"),
                                  bg="#1e40af", fg="white")
        self.temp_label.grid(row=1, column=0, sticky="w", padx=20, pady=20)
        
        # Weather info 
        weather_info_frame = tk.Frame(weather_frame, bg="#1e40af")
        weather_info_frame.grid(row=1, column=1, sticky="w", padx=20, pady=20)
        
        self.city_label = tk.Label(weather_info_frame, text="Loading...",
                                  font=("Segoe UI", 16, "bold"),
                                  bg="#1e40af", fg="white")
        self.city_label.grid(row=0, column=0, sticky="w")
        
        self.desc_label = tk.Label(weather_info_frame, text="",
                                  font=("Segoe UI", 12),
                                  bg="#1e40af", fg="#cbd5e1")
        self.desc_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Weather icon 
        self.icon_label = tk.Label(weather_frame, text="❓",
                                  font=("Segoe UI", 48),
                                  bg="#1e40af")
        self.icon_label.grid(row=1, column=2, sticky="e", padx=20, pady=20)
        
        # Weather details 
        self.details_frame = tk.Frame(weather_frame, bg="#1e40af")
        self.details_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=10)
    
    def create_forecast_section(self, parent):      
        forecast_frame = tk.Frame(parent, bg="#374151", relief="solid", bd=2)
        forecast_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))
        forecast_frame.grid_rowconfigure(1, weight=1)
        forecast_frame.grid_columnconfigure(0, weight=1)
        
        header_label = tk.Label(forecast_frame, text="📅 5-Day Forecast",
                            font=("Segoe UI", 16, "bold"),
                            bg="#374151", fg="white")
        header_label.grid(row=0, column=0, pady=10)
        
        # Forecast items container 
        self.forecast_items_frame = tk.Frame(forecast_frame, bg="#374151")
        self.forecast_items_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 15))
        
        # Configure grid weights 
        self.forecast_items_frame.grid_rowconfigure(0, weight=1)
        for i in range(5):
            self.forecast_items_frame.grid_columnconfigure(i, weight=1, uniform="forecast")
    
    def create_weather_map_section(self, parent):     
        map_frame = tk.Frame(parent, bg="white", relief="solid", bd=2)
        map_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(5, 0))
        map_frame.grid_rowconfigure(1, weight=1)
        map_frame.grid_columnconfigure(0, weight=1)       
        
        header_label = tk.Label(map_frame, text="📈 Temperature Trend",
                               font=("Segoe UI", 16, "bold"),
                               bg="white", fg="#1f2937")
        header_label.grid(row=0, column=0, pady=10)
        
        # Graph container
        self.graph_container = tk.Frame(map_frame, bg="white")
        self.graph_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
    
    def create_activity_tracker_section(self, parent):        
        activity_frame = tk.Frame(parent, bg="#f3f4f6", relief="solid", bd=2)
        activity_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(5, 0))
        activity_frame.grid_rowconfigure(1, weight=1)
        activity_frame.grid_columnconfigure(0, weight=1)
        
        header_label = tk.Label(activity_frame, text="🎯 Activity Suggestions",
                               font=("Segoe UI", 16, "bold"),
                               bg="#f3f4f6", fg="#1f2937")
        header_label.grid(row=0, column=0, pady=10)
        
        # Activity content
        self.activity_content_frame = tk.Frame(activity_frame, bg="#f3f4f6")
        self.activity_content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Default activity suggestions
        self.create_default_activities()
    
    def create_default_activities(self):      
        activities = ["🚶 Take a Walk", "☕ Coffee Break", "📚 Reading Time", "🏠 Indoor Activities"]
        
        for i, activity in enumerate(activities):
            btn = tk.Button(self.activity_content_frame, text=activity,
                           font=("Segoe UI", 12), bg="#e5e7eb", fg="#374151",
                           relief="flat", pady=10, cursor="hand2",
                           command=lambda a=activity: self.display_activity_detail(a))
            btn.grid(row=i, column=0, sticky="ew", pady=5, padx=10)
            self.activity_content_frame.grid_columnconfigure(0, weight=1)
    
    def create_graphs_tab(self):    
        graphs_frame = ttk.Frame(self.notebook)
        self.notebook.add(graphs_frame, text="📊 Charts & Graphs")
        
        try:
            self.graphs_panel = GraphsAndChartsPanel(graphs_frame, self.db, 
                                                   self.logger, self.theme_manager)
        except Exception as e:
            self.logger.error(f"Error initializing graphs panel: {e}")
            error_label = tk.Label(graphs_frame, text="📊 Charts & Graphs\n\nGraphs panel will load here",
                                  font=("Segoe UI", 16), bg="#f8fafc", fg="#6b7280")
            error_label.pack(expand=True)
    
    def create_trends_tab(self):       
        trends_frame = ttk.Frame(self.notebook)
        self.notebook.add(trends_frame, text="📈 Trends")
        
        try:
            self.trends_panel = TrendPanel(trends_frame, self.db, self.logger, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing trends panel: {e}")
            error_label = tk.Label(trends_frame, text="📈 Weather Trends\n\nTrends analysis will appear here",
                                  font=("Segoe UI", 16), bg="#f8fafc", fg="#6b7280")
            error_label.pack(expand=True)
    
    def create_statistics_tab(self):       
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistics")
        
        try:
            self.stats_panel = SimpleStatsPanel(stats_frame, fetcher=self.fetcher, db=self.db, logger=self.logger, tracker=self.tracker, cfg=self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing stats panel: {e}")
            # Create manual stats display
            self.create_manual_stats_display(stats_frame)
    
    def create_manual_stats_display(self, parent):
        stats_container = tk.Frame(parent, bg="#f8fafc")
        stats_container.pack(fill="both", expand=True, padx=20, pady=20)
        
    
        title_label = tk.Label(stats_container, text="📊 Weather Statistics",
                              font=("Segoe UI", 20, "bold"),
                              bg="#f8fafc", fg="#1f2937")
        title_label.pack(pady=(0, 20))
        
     
        controls_frame = tk.Frame(stats_container, bg="#f8fafc")
        controls_frame.pack(fill="x", pady=(0, 20))
        
        refresh_btn = tk.Button(controls_frame, text="🔄 Refresh Stats",
                               font=("Segoe UI", 12, "bold"),
                               bg="#3b82f6", fg="white", padx=20, pady=10,
                               cursor="hand2", command=self.display_statistics)
        refresh_btn.pack(side="left", padx=(0, 10))
        
        export_btn = tk.Button(controls_frame, text="💾 Export Data",
                              font=("Segoe UI", 12, "bold"),
                              bg="#f59e0b", fg="white", padx=20, pady=10,
                              cursor="hand2", command=self.export_data)
        export_btn.pack(side="left")
        
        # Stats display
        self.stats_display = tk.Frame(stats_container, bg="white", relief="solid", bd=1)
        self.stats_display.pack(fill="both", expand=True)
        
        self.stats_label = tk.Label(self.stats_display, text="Loading statistics...",
                                   font=("Segoe UI", 12), bg="white", fg="#374151")
        self.stats_label.pack(padx=20, pady=20, anchor="w")
    
    def create_favorites_tab(self):      
        favorites_frame = ttk.Frame(self.notebook)
        self.notebook.add(favorites_frame, text="⭐ Favorites")
        
        try:
            self.favorites_panel = FavoriteCityPanel(favorites_frame, self.tracker, 
                                                   self.db, self.logger, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing favorites panel: {e}")
            error_label = tk.Label(favorites_frame, text="⭐ Favorite Cities\n\nFavorites manager will appear here",
                                  font=("Segoe UI", 16), bg="#f8fafc", fg="#6b7280")
            error_label.pack(expand=True)
    
    def create_journal_tab(self):      
        journal_frame = ttk.Frame(self.notebook)
        self.notebook.add(journal_frame, text="📓 Journal")
        
        try:
            self.journal_panel = JournalPanel(journal_frame, self.get_city, self.logger, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing journal panel: {e}")
            error_label = tk.Label(journal_frame, text="📓 Weather Journal\n\nJournal entries will appear here",
                                  font=("Segoe UI", 16), bg="#f8fafc", fg="#6b7280")
            error_label.pack(expand=True)
    
    def create_guess_tab(self):     
        guess_frame = ttk.Frame(self.notebook)
        self.notebook.add(guess_frame, text="🔮 Tomorrow's Guess")
        
        try:
            self.guess_panel = TomorrowGuessPanel(guess_frame, self.db, self.logger, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing guess panel: {e}")
            error_label = tk.Label(guess_frame, text="🔮 Tomorrow's Weather Guess\n\nPredictions will appear here",
                                  font=("Segoe UI", 16), bg="#f8fafc", fg="#6b7280")
            error_label.pack(expand=True)
    
    def create_compare_tab(self): 
        compare_frame = ttk.Frame(self.notebook)
        self.notebook.add(compare_frame, text="🏙️ Compare Cities")
        
        try:
            self.compare_panel = CityComparisonPanel(compare_frame, self.db, self.fetcher, self.logger)
        except Exception as e:
            self.logger.error(f"Error initializing compare panel: {e}")
            error_label = tk.Label(compare_frame, text="🏙️ Compare Cities\n\nCity comparisons will appear here",
                                  font=("Segoe UI", 16), bg="#f8fafc", fg="#6b7280")
            error_label.pack(expand=True)
    
    def create_activity_tab(self):     
        activity_frame = ttk.Frame(self.notebook)
        self.notebook.add(activity_frame, text="🎯 Activity Suggestions")
        
        try:
            self.activity_panel = ActivityPanel(activity_frame, self.fetcher, self.db, 
                                               self.logger, self.tracker, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing activity panel: {e}")
            error_label = tk.Label(activity_frame, text="🎯 Activity Suggestions\n\nActivity recommendations will appear here",
                                  font=("Segoe UI", 16), bg="#f8fafc", fg="#6b7280")
            error_label.pack(expand=True)
    
    def get_weather_threaded(self):      
        threading.Thread(target=self.get_weather, daemon=True).start()

    def get_weather(self):      
        city = self.city_entry.get().strip() or "Knoxville"
        country = self.country_entry.get().strip() or "US"
        
        # Determine units based on country
        units = "imperial" if country.upper() == "US" else "metric"
        
        try:
            # Update UI to show loading
            self.root.after(0, lambda: self.temp_label.config(text="Loading..."))
            self.root.after(0, lambda: self.city_label.config(text=f"{city}, {country}"))
            
            # Fetch current weather
            current_weather = self.fetcher.fetch_current_weather(city, country, units)
            if current_weather:
                self.current_weather_data = current_weather
                self.db.insert_reading(current_weather)
                
                # Update current weather display
                self.root.after(0, lambda: self.display_current_weather(current_weather))
                
                # Fetch and display forecast 
                forecast_data = self.fetcher.fetch_five_day_forecast(city, country, units)
                if forecast_data:
                    # Use the extract_five_day_summary 
                    daily_forecasts = self.extract_five_day_summary(forecast_data)
                    self.root.after(0, lambda: self.display_forecast(daily_forecasts, units))
                
                # Update activity suggestions
                self.root.after(0, lambda: self.update_activity_suggestions(current_weather))
                
                # Update temperature graph
                self.root.after(0, lambda: self.update_temperature_graph(city, country))
                
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Could not fetch weather data"))
                
        except Exception as e:
            self.logger.error(f"Weather fetch error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Weather fetch failed: {e}"))

    def extract_five_day_summary(self, forecast):     
        forecast_list = forecast.get("list", [])
        daily_data = defaultdict(list)

        # Organize forecast data 
        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if dt_txt:
                date = dt_txt.split(" ")[0]
                daily_data[date].append(entry)

        five_day_forecasts = []

        # Get forecasts 5 days
        for date in sorted(daily_data.keys())[:5]:
            entries = daily_data[date]
            preferred_entry = next(
                (e for e in entries if "12:00:00" in e["dt_txt"]),
                entries[len(entries)//2]  # fallback to middle of the day
            )
            five_day_forecasts.append(preferred_entry)

        return five_day_forecasts

    def display_forecast(self, forecast_list, units="metric"):       
        # Clear existing forecast
        for widget in self.forecast_items_frame.winfo_children():
            widget.destroy()
        
        if not forecast_list:
            return
        
        for i in range(5):
            self.forecast_items_frame.grid_columnconfigure(i, weight=1, uniform="forecast")
        
        today = datetime.now()
        for i, forecast in enumerate(forecast_list):
            try:
                day = today + timedelta(days=i)
                day_name = "Today" if i == 0 else day.strftime("%A")[:3]
                
                # Forecast item
                item_frame = tk.Frame(self.forecast_items_frame, bg="#4b5563", relief="raised", bd=1)
                item_frame.grid(row=0, column=i, padx=3, pady=5, sticky="nsew", ipady=15, ipadx=10)
                
                # Day label
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

    def display_current_weather(self, weather_data):
        try:
            # Get temperature and unit from the data
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
        
            weather_main = weather_data.get("weather_summary", "Clear")
            icon_path = get_icon_path(weather_main)
            emoji = WeatherEmoji.get_weather_emoji(weather_main)
            
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

    def update_weather_details(self, weather_data):      
        # Clear existing details
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        details = []
        
        # Determine temperature unit
        country = self.country_entry.get().strip() or "US"
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
            detail_label = tk.Label(self.details_frame, text=detail, 
                                bg="#1e40af", fg="#9ca3af", 
                                font=("Segoe UI", 10))
            detail_label.grid(row=0, column=i, padx=10, sticky="w")
        
    def update_activity_suggestions(self, weather_data):
        # Clear existing activities
        for widget in self.activity_content_frame.winfo_children():
            widget.destroy()
        
        try:
            temp_c = weather_data['temp']
            temp_f = (temp_c)
            condition = weather_data['weather_summary'].lower()
            
            # Get weather activities
            if temp_f > 75:
                activities = ["🏊 Swimming", "🚴 Bike Ride", "🌳 Park Visit", "🍦 Ice Cream"]
            elif temp_f > 60:
                activities = ["🚶 Nature Walk", "☕ Outdoor Café", "📸 Photography", "🛍️ Shopping"]
            elif temp_f > 40:
                activities = ["🏛️ Museum", "☕ Coffee Shop", "🎬 Movies", "🏠 Indoor Gym"]
            else:
                activities = ["🏠 Stay Cozy", "📚 Reading", "🍳 Cooking", "🎮 Gaming"]
            
            # Adjust for weather conditions
            if "rain" in condition:
                activities = ["☔ Indoor Mall", "🏠 Home Projects", "☕ Coffee Shop", "🎬 Movies"]
            elif "snow" in condition:
                activities = ["⛄ Snow Fun", "🏠 Warm Inside", "☕ Hot Drinks", "🔥 Fireplace"]
            
            # Create activity buttons
            for i, activity in enumerate(activities):
                btn = tk.Button(self.activity_content_frame, text=activity,
                               font=("Segoe UI", 11), bg="#e8f4fd", fg="#2c3e50",
                               relief="flat", pady=8, cursor="hand2",
                               command=lambda a=activity: self.display_activity_detail(a))
                btn.grid(row=i, column=0, sticky="ew", pady=3, padx=10)
                self.activity_content_frame.grid_columnconfigure(0, weight=1)
                
        except Exception as e:
            self.logger.error(f"Error updating activities: {e}")
    
    def update_temperature_graph(self, city, country):
        try:
            # Clear existing graph
            for widget in self.graph_container.winfo_children():
                widget.destroy()
            
            # Get recent readings 
            readings = self.db.fetch_recent(city, country, hours=24)
            
            if readings and len(readings) > 1:
                # Convert readings to DataFrame with datetime handling
                df = pd.DataFrame(readings)
                
                # Ensure timestamp is datetime
                if 'timestamp' in df.columns:
                    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                        # Try to convert string timestamps
                        try:
                            df['timestamp'] = pd.to_datetime(df['timestamp'])
                        except:
                            # If that fails, try unix timestamp
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                
                # Create matplotlib figure with subplots
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 4), sharex=True)
                
                # Convert temperature to Fahrenheit for US
                temps = df['temp'].tolist()
                if country.upper() == "US":
                    temps = [(t) for t in temps]
                    temp_unit = "°F"
                else:
                    temp_unit = "°C"
                
                times = df['timestamp'].tolist()
                
                # Top plot: Temperature
                ax1.plot(times, temps, color='#ef4444', linewidth=2, marker='o', markersize=3)
                ax1.set_ylabel(f'Temperature ({temp_unit})', color='#ef4444')
                ax1.tick_params(axis='y', labelcolor='#ef4444')
                ax1.grid(True, alpha=0.3)
                ax1.set_title('Weather Metrics - Last 24 Hours', fontsize=10, pad=10)
                
                # Bottom plot: Humidity and Pressure
                if 'humidity' in df.columns and 'pressure' in df.columns:
                    humidity = df['humidity'].tolist()
                    pressure = df['pressure'].tolist()
                    
                    # Plot humidity
                    color = '#3b82f6'
                    ax2.plot(times, humidity, color=color, linewidth=2, marker='s', markersize=3, label='Humidity (%)')
                    ax2.set_ylabel('Humidity (%)', color=color)
                    ax2.tick_params(axis='y', labelcolor=color)
                    
                    # Create second y-axis for pressure
                    ax2_twin = ax2.twinx()
                    color = '#10b981'
                    ax2_twin.plot(times, pressure, color=color, linewidth=2, marker='^', markersize=3, label='Pressure (hPa)')
                    ax2_twin.set_ylabel('Pressure (hPa)', color=color)
                    ax2_twin.tick_params(axis='y', labelcolor=color)
                    
                else:
                    # Fallback to just humidity if pressure not available
                    if 'humidity' in df.columns:
                        humidity = df['humidity'].tolist()
                        ax2.plot(times, humidity, color='#3b82f6', linewidth=2, marker='s', markersize=3)
                        ax2.set_ylabel('Humidity (%)')
                    else:
                        ax2.text(0.5, 0.5, 'Additional data unavailable', 
                                transform=ax2.transAxes, ha='center', va='center')
                
                ax2.grid(True, alpha=0.3)
                
                # Format x-axis
                ax2.xaxis.set_major_formatter(DateFormatter('%H:%M'))
                ax2.xaxis.set_major_locator(HourLocator(interval=6))
                
                # Rotate x-axis labels
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
                
                fig.tight_layout()
                
                # Embed in tkinter
                canvas = FigureCanvasTkAgg(fig, self.graph_container)
                canvas.draw()
                canvas.get_tk_widget().pack(fill='both', expand=True)
                
            else:
                # Show placeholder
                placeholder = tk.Label(self.graph_container,
                                    text="📊 Weather metrics will appear\nafter more data is collected",
                                    font=("Segoe UI", 12), bg="white", fg="#6b7280")
                placeholder.pack(expand=True)
                
        except Exception as e:
            self.logger.error(f"Error updating graph: {e}")
            error_label = tk.Label(self.graph_container,
                                text="Graph temporarily unavailable",
                                font=("Segoe UI", 12), bg="white", fg="#e74c3c")
            error_label.pack(expand=True)



        
    
    def display_activity_detail(self, activity):    
        messagebox.showinfo("Activity Suggestion", 
                          f"Great choice! {activity} is perfect for today's weather conditions.\n\n"
                          f"Enjoy your activity and stay safe!")
    
    def display_statistics(self) -> None:
        """Display weather statistics based on entry fields."""
        try:
            if not all([
                hasattr(self, "city_entry"), hasattr(self, "state_entry"),
                hasattr(self, "country_entry"), hasattr(self, "stats_label")
            ]):
                self.logger.error("One or more input fields are not initialized.")
                if hasattr(self, "stats_label"):
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
            if hasattr(self, "stats_label"):
                self.stats_label.config(text=f"❌ Error: {str(e)}")
                
            
    def show_statistics(self) -> None:
        """Show weather statistics using the callback and default location data."""
        try:
            city = self.get_city_callback() if hasattr(self, "get_city_callback") else "Knoxville"
            state = "TN"  # You can replace this with a dynamic value if desired
            country = "US"

            stats_text = get_weather_stats(self.db, city, state, country)

            if hasattr(self, "stats_label") and self.stats_label:
                self.stats_label.config(
                    text=f"📊 Statistics for {city}, {state}, {country}:\n\n{stats_text}"
                )

        except Exception as e:
            self.logger.error(f"Error showing statistics: {e}")
            if hasattr(self, "stats_label") and self.stats_label:
                self.stats_label.config(text=f"❌ Error loading statistics: {str(e)}")

    def export_data(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save weather data as..."
            )
            
            if filename:
                success = self.db.export_readings_to_csv(filename)
                if success:
                    messagebox.showinfo("Export Successful", 
                                      f"Weather data exported to:\n{filename}")
                else:
                    messagebox.showwarning("Export Failed", 
                                         "No weather records available to export.")
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")
    
    def get_city(self):    
        return self.city_entry.get().strip() or "Knoxville"
    
    def toggle_theme(self):      
        try:
            new_theme = self.theme_manager.toggle_theme()
            self.logger.info(f"Theme switched to: {new_theme}")
        except Exception as e:
            self.logger.error(f"Theme toggle error: {e}")
    
    def update_time(self):
        if self.root.winfo_exists():  # Check if window still exists
            current_time = datetime.now().strftime("%I:%M %p")
            self.time_label.config(text=current_time)
            self.root.after(60000, self.update_time)
        
    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.logger.info("Weather Dashboard application closing")

# from components.creater_header import CreateHeader
# from components.create_feature_tabs import CreateFeatureTabs
# from components.display_features_ui import DisplayFeatures
# from components.get_weather import GetWeather
# from collections import defaultdict, Counter


# from datetime import datetime, timedelta, timezone
# import os
# from matplotlib.container import BarContainer
# import matplotlib.cm as cm
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.dates import DateFormatter, HourLocator
# import matplotlib.dates as mdates
# import tkinter as tk
# from tkinter import ttk, messagebox, filedialog
# from PIL import Image, ImageTk
# import threading
# import pandas as pd
# from matplotlib.dates import DateFormatter, HourLocator
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from dotenv import load_dotenv
# from config import Config
# from config import setup_logger
# from typing import cast, Optional
# from components.create_dashboard_layout_ui import CreateDashboardLayout
# from features.activity.activity_panel import ActivityPanel
# from features.simple_statistics import get_weather_stats
# from features.weather_icons import display_weather_with_icon, get_icon_path, icon_map
# from features.simple_statistics import SimpleStatsPanel
# import requests
# from weather_data_fetcher import WeatherDataFetcher
# from features.city_comparisons import CityComparisonPanel
# from features.favorites_manager import FavoriteCityPanel
# from features.theme_switcher import ThemeManager
# from features.activity.activity_suggester import ActivitySuggester
# from features.tomorrows_guess import TomorrowGuessPanel
# from features.weather_journal import JournalPanel
# from features.trends import TrendPanel
# from utils.date_time_utils import format_local_time
# from features.graphs_and_charts import WeatherGraphs, GraphsAndChartsPanel
# from utils.emoji import WeatherEmoji
# from services.weather_stats import get_weather_stats
# from features.theme_switcher import ThemeManager
# load_dotenv()
# cfg = Config.load_from_env()
# class WeatherAppGUI:
#     def __init__(self, fetcher, db, tracker, logger, cfg):
#         self.fetcher = fetcher
#         self.db = db
#         self.tracker = tracker
#         self.logger = logger
#         self.cfg = cfg
#         self.current_weather_data = None
        
#         # Create main window
#         self.root = tk.Tk()
#         self.root.title("🌤️ Weather Dashboard Pro")
#         self.root.geometry("1600x1000")
#         self.root.configure(bg="#f8fafc")
        
#         # Configure main grid
#         self.root.grid_rowconfigure(1, weight=1)
#         self.root.grid_columnconfigure(0, weight=1)
        
#         # Initialize theme manager
#         self.theme_manager = ThemeManager(self.root)
#         self.weather_graphs = WeatherGraphs(self.theme_manager)
        
        
#         self.header = CreateHeader(
#             root=self.root,
#             get_weather_callback=self.get_weather_threaded,
#             toggle_theme_callback=self.toggle_theme
#         )
#         city, country = self.header.get_location()
        

#         # self.create_header()
#         # self.create_tab_interface()
        
#         self.root.after(1000, self.get_weather_threaded)
#         self.summary_label = ttk.Label(self.root, text="", font=("Segoe UI", 10), foreground="#334155")
#         self.summary_label.grid(row=2, column=0, sticky="w", padx=20, pady=(10, 0))
#         self.display_features.display_current_weather(weather_data)
    
    
#             # In your weather update method
#         self.display_features = DisplayFeatures(
#             parent=self.root,
#             theme_manager=self.theme_manager,
#             db=self.db,
#             logger=self.logger,
#             fetcher=self.fetcher,
#             cfg=self.cfg,
#             city_entry=self.city_entry,
#             country_entry=self.country_entry
#         )
        
#         self.display_features.set_ui_references(
#             temp_label=self.widgets.get('temp_label'),
#             city_label=self.widgets.get('city_label'),
#             desc_label=self.widgets.get('desc_label'),
#             icon_label=self.widgets.get('icon_label'),
#             details_frame=self.widgets.get('details_frame'),
#             forecast_items_frame=self.widgets.get('forecast_items_frame'),
#             hourly_scroll_frame=self.widgets.get('hourly_scroll_frame'),
#             graph_container=self.widgets.get('graph_container'),
#             activity_content_frame=self.widgets.get('activity_content_frame')
#         )
# weather_data = your_weather_api.get_current_weather(city, country)
# self.display_features.display_current_weather(weather_data)

# forecast_data = your_weather_api.get_forecast(city, country)
# self.display_features.display_forecast(forecast_data, units="imperial")