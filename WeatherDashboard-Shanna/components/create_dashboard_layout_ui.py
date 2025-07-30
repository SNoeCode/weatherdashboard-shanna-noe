from typing import Dict, Optional, Union
import tkinter as tk
import os
from PIL import Image, ImageTk
from features.weather_icons import get_icon_path
from config import Config
cfg = Config.load_from_env()
class CreateDashboardLayout:   
    def __init__(self, parent, theme_manager, db, logger, fetcher,cfg):
        self.parent = parent
        self.theme_manager = theme_manager
        self.db = db
        self.logger = logger
        self.fetcher = fetcher
        
   
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

    def create_dashboard_layout(self, dashboard_frame):
        """Creates the main 2x3 dashboard grid layout"""
        # Configure grid for 2x3 layout (2 rows, 3 columns)
        dashboard_frame.grid_rowconfigure(0, weight=1)
        dashboard_frame.grid_rowconfigure(1, weight=1)
        dashboard_frame.grid_columnconfigure(0, weight=1)
        dashboard_frame.grid_columnconfigure(1, weight=1)
        dashboard_frame.grid_columnconfigure(2, weight=1)
        
        # Create all sections
        self.create_current_weather_section(dashboard_frame)    # Top Left
        self.create_forecast_section(dashboard_frame)           # Top Center  
        self.create_hourly_forecast_section(dashboard_frame)    # Top Right
        self.create_weather_graph_section(dashboard_frame)      # Bottom Left
        self.create_activity_suggestions_section(dashboard_frame) # Bottom Center & Right

    def create_current_weather_section(self, parent):
        """Creates the current weather display section"""
        weather_frame = tk.Frame(parent, bg="#1e40af", relief="solid", bd=2)
        weather_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        weather_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        header_label = tk.Label(weather_frame, text="🌡️ Current Weather", 
                               font=("Segoe UI", 16, "bold"),
                               bg="#1e40af", fg="white")
        header_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Temperature display
        self.widgets['temp_label'] = tk.Label(weather_frame, text="--°F", 
                                             font=("Segoe UI", 48, "bold"),
                                             bg="#1e40af", fg="white")
        self.widgets['temp_label'].grid(row=1, column=0, sticky="w", padx=20, pady=20)
        
        # Weather info section
        weather_info_frame = tk.Frame(weather_frame, bg="#1e40af")
        weather_info_frame.grid(row=1, column=1, sticky="w", padx=20, pady=20)
        
        self.widgets['city_label'] = tk.Label(weather_info_frame, text="Loading...",
                                             font=("Segoe UI", 16, "bold"),
                                             bg="#1e40af", fg="white")
        self.widgets['city_label'].grid(row=0, column=0, sticky="w")
        
        self.widgets['desc_label'] = tk.Label(weather_info_frame, text="",
                                             font=("Segoe UI", 12),
                                             bg="#1e40af", fg="#cbd5e1")
        self.widgets['desc_label'].grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Weather icon
        self.widgets['icon_label'] = tk.Label(weather_frame, text="❓",
                                             font=("Segoe UI", 48),
                                             bg="#1e40af")
        self.widgets['icon_label'].grid(row=1, column=2, sticky="e", padx=20, pady=20)
        
        # Weather details container
        self.widgets['details_frame'] = tk.Frame(weather_frame, bg="#1e40af")
        self.widgets['details_frame'].grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=10)

    def create_forecast_section(self, parent):
        """Creates the 5-day forecast section"""
        forecast_frame = tk.Frame(parent, bg="#374151", relief="solid", bd=2)
        forecast_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=(0, 5))
        forecast_frame.grid_rowconfigure(1, weight=1)
        forecast_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = tk.Label(forecast_frame, text="📅 5-Day Forecast",
                               font=("Segoe UI", 16, "bold"),
                               bg="#374151", fg="white")
        header_label.grid(row=0, column=0, pady=10)
        
        # Forecast items container
        self.widgets['forecast_items_frame'] = tk.Frame(forecast_frame, bg="#374151")
        self.widgets['forecast_items_frame'].grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 15))
        
        # Configure grid weights for uniform columns
        self.widgets['forecast_items_frame'].grid_rowconfigure(0, weight=1)
        for i in range(5):
            self.widgets['forecast_items_frame'].grid_columnconfigure(i, weight=1, uniform="forecast")

    def create_hourly_forecast_section(self, parent):
        """Creates the hourly forecast section (NEW FEATURE)"""
        hourly_frame = tk.Frame(parent, bg="#065f46", relief="solid", bd=2)
        hourly_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=(0, 5))
        hourly_frame.grid_rowconfigure(1, weight=1)
        hourly_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = tk.Label(hourly_frame, text="⏰ Hourly Forecast",
                               font=("Segoe UI", 16, "bold"),
                               bg="#065f46", fg="white")
        header_label.grid(row=0, column=0, pady=10)
        
        # Scrollable hourly forecast container
        self.widgets['hourly_scroll_frame'] = tk.Frame(hourly_frame, bg="#065f46")
        self.widgets['hourly_scroll_frame'].grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 15))

    def create_weather_graph_section(self, parent):
        """Creates the temperature trend graph section"""
        map_frame = tk.Frame(parent, bg="white", relief="solid", bd=2)
        map_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(5, 0))
        map_frame.grid_rowconfigure(1, weight=1)
        map_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = tk.Label(map_frame, text="📈 Temperature Trend",
                               font=("Segoe UI", 16, "bold"),
                               bg="white", fg="#1f2937")
        header_label.grid(row=0, column=0, pady=10)
        
        # Graph container
        self.widgets['graph_container'] = tk.Frame(map_frame, bg="white")
        self.widgets['graph_container'].grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def create_activity_suggestions_section(self, parent):
        """Creates compact activity suggestions section"""
        activity_frame = tk.Frame(parent, bg="#f3f4f6", relief="solid", bd=2)
        activity_frame.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=(5, 0), pady=(5, 0))
        activity_frame.grid_rowconfigure(1, weight=1)
        activity_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = tk.Label(activity_frame, text="🎯 Activity Suggestions",
                               font=("Segoe UI", 16, "bold"),
                               bg="#f3f4f6", fg="#1f2937")
        header_label.grid(row=0, column=0, pady=10)
        
        # Activity content container
        self.widgets['activity_content_frame'] = tk.Frame(activity_frame, bg="#f3f4f6")
        self.widgets['activity_content_frame'].grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Initialize with default activities
        self.create_default_activities()
    def create_default_activities(self):
        """Creates default activity suggestion buttons"""
        activities = ["🚶 Take a Walk", "☕ Coffee Break", "📚 Reading Time", "🏠 Indoor Activities"]
        activity_frame = self.widgets.get('activity_content_frame')

        for i, activity in enumerate(activities):
            btn = tk.Button(
                activity_frame,
                text=activity,
                font=("Segoe UI", 10),
                bg="#e5e7eb",
                fg="#374151",
                relief="flat",
                pady=8,
                cursor="hand2"
            )
            btn.grid(row=0, column=i, sticky="ew", padx=5, pady=5)

            if activity_frame:
                activity_frame.grid_columnconfigure(i, weight=1)

    def get_widget(self, widget_name):
        """Returns a widget reference by name"""
        return self.widgets.get(widget_name)

    def clear_widget(self, widget_name):
        """Clears all children from a widget"""
        widget = self.widgets.get(widget_name)
        if widget:
            for child in widget.winfo_children():
                child.destroy()




