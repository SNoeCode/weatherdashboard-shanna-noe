from typing import Dict, Optional, Union
import tkinter as tk
import tkinter.ttk as ttk  # Add this import for scrollbar
import os
import datetime
from features.emoji import WeatherEmoji
from PIL import Image, ImageTk
from features.weather_icons import WeatherIconManager
from config import Config
from components.get_weather import GetWeather
cfg = Config.load_from_env()

class CreateDashboardLayout:   
    def __init__(self, parent, theme_manager, db, logger, fetcher, cfg):
        self.parent = parent
        self.theme_manager = theme_manager
        self.db = db
        self.logger = logger
        self.fetcher = fetcher
        self.cfg = cfg
        self.current_weather_data = None
        
        # Icon mapping with your custom icons
        self.icon_map = {
            "Clear": "icons/icons8-sun-50.png",
            "Rain": "icons/icons8-rain-50.png", 
            "Thunderstorm": "icons/icons8-thunderstorm-100.png",
            "Clouds": "icons/icons8-clouds-50.png",
            "Snow": "icons/icons8-snow-50.png",
            "Wind": "icons/icons8-windy-weather-50.png",
            "Mist": "icons/weather_icons_dovora_interactive/PNG/128/mist.png",
            "Drizzle": "icons/icons8-rain-50.png",
            "Fog": "icons/weather_icons_dovora_interactive/PNG/128/mist.png",
            "Haze": "icons/weather_icons_dovora_interactive/PNG/128/mist.png"
        }
        
        # Widget references
        self.widgets = {
            'temp_label': None,
            'city_label': None,
            'desc_label': None,
            'icon_label': None,
            'details_frame': None,
            'forecast_items_frame': None,
            'hourly_scroll_frame': None,
            'graph_container': None
        }
        
        # UI element references for integration
        self.city_entry = None
        self.country_entry = None
        
    def set_ui_references(self, city_entry=None, country_entry=None):
        """Set references to UI input elements"""
        if city_entry:
            self.city_entry = city_entry
        if country_entry:
            self.country_entry = country_entry

    def create_dashboard_layout(self, dashboard_frame=None):
        """Creates the main 2x2 dashboard grid layout with 4 sections"""
        if dashboard_frame is None:
            dashboard_frame = self.parent
            
        # Configure grid for 2x2 layout (2 rows, 2 columns)
        dashboard_frame.grid_rowconfigure(0, weight=1)
        dashboard_frame.grid_rowconfigure(1, weight=1)
        dashboard_frame.grid_columnconfigure(0, weight=1)
        dashboard_frame.grid_columnconfigure(1, weight=1)
        
        # Create all 4 sections in 2x2 grid
        self.create_current_weather_section(dashboard_frame)    # Top Left (0,0)
        self.create_forecast_section(dashboard_frame)           # Top Right (0,1)  
        self.create_weather_graph_section(dashboard_frame)      # Bottom Left (1,0)
        self.create_hourly_forecast_section(dashboard_frame)    # Bottom Right (1,1)
        
    def create_current_weather_section(self, parent):      
        weather_frame = tk.Frame(parent, bg="#1e40af", relief="solid", bd=2)
        weather_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        weather_frame.grid_columnconfigure(1, weight=1)
        
        header_label = tk.Label(weather_frame, text="🌡️ Current Weather", 
                               font=("Segoe UI", 16, "bold"),
                               bg="#1e40af", fg="white")
        header_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Temperature 
        self.widgets['temp_label'] = tk.Label(weather_frame, text="--°F", 
                                            font=("Segoe UI", 48, "bold"),
                                            bg="#1e40af", fg="white")
        self.widgets['temp_label'].grid(row=1, column=0, sticky="w", padx=20, pady=20)
        
        # Weather info 
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
        
        self.widgets['details_frame'] = tk.Frame(weather_frame, bg="#1e40af")
        self.widgets['details_frame'].grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=10)

    def create_forecast_section(self, parent):      
        forecast_frame = tk.Frame(parent, bg="#374151", relief="solid", bd=2)         
        forecast_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))         
        forecast_frame.grid_rowconfigure(1, weight=1)         
        forecast_frame.grid_columnconfigure(0, weight=1)          

        header_label = tk.Label(forecast_frame, text="📅 5-Day Forecast",                                 
                            font=("Segoe UI", 16, "bold"),                                 
                            bg="#374151", fg="white")         
        header_label.grid(row=0, column=0, pady=10)          

        # Create forecast items frame with proper configuration
        self.widgets['forecast_items_frame'] = tk.Frame(forecast_frame, bg="#374151")         
        self.widgets['forecast_items_frame'].grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 12))          

        # Configure the forecast items frame grid
        self.widgets['forecast_items_frame'].grid_rowconfigure(0, weight=1)         
        for i in range(5):             
            self.widgets['forecast_items_frame'].grid_columnconfigure(i, weight=1, uniform="forecast")
    def create_weather_graph_section(self, parent):
        graph_frame = tk.Frame(parent, bg="white", relief="solid", bd=2)
        graph_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(5, 0))  # Bottom Left
        graph_frame.grid_rowconfigure(1, weight=1)
        graph_frame.grid_columnconfigure(0, weight=1)
           
        header_label = tk.Label(graph_frame, text="📈 Temperature Trend",
                               font=("Segoe UI", 16, "bold"),
                               bg="white", fg="#1f2937")
        header_label.grid(row=0, column=0, pady=10)
              
        self.widgets['graph_container'] = tk.Frame(graph_frame, bg="white")
        self.widgets['graph_container'].grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
 
    def create_default_hourly_message(self):      
        scroll_frame = None
        
        if hasattr(self, 'widgets') and self.widgets and 'hourly_scroll_frame' in self.widgets:
            scroll_frame = self.widgets['hourly_scroll_frame']
        elif hasattr(self, 'hourly_scroll_frame'):
            scroll_frame = self.hourly_scroll_frame
        
        if scroll_frame:
            default_label = tk.Label(scroll_frame,
                                text="🕐 Hourly forecast will appear here\nafter weather data is fetched",
                                font=("Segoe UI", 12), bg="#f8fafc", fg="#6b7280")
            default_label.pack(expand=True, pady=20)

    def create_hourly_forecast_section(self, parent):
        hourly_frame = tk.Frame(parent, bg="#f8fafc", relief="solid", bd=2)
        hourly_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(5, 0))
        hourly_frame.grid_rowconfigure(1, weight=1)
        hourly_frame.grid_columnconfigure(0, weight=1)
      
        header_label = tk.Label(hourly_frame, text="🕐 Hourly Forecast",
                            font=("Segoe UI", 16, "bold"),
                            bg="#f8fafc", fg="#1f2937")
        header_label.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        # Calculate dimensions based on 2000x1200 root window
        canvas_height = 180 
    
        canvas = tk.Canvas(hourly_frame, bg="#f8fafc", highlightthickness=0, height=canvas_height)
        h_scrollbar = ttk.Scrollbar(hourly_frame, orient="horizontal", command=canvas.xview)
    
        scroll_frame = tk.Frame(canvas, bg="#f8fafc")        
       
        if hasattr(self, 'widgets') and self.widgets is not None:
            self.widgets['hourly_scroll_frame'] = scroll_frame
        self.hourly_scroll_frame = scroll_frame
       
        def update_scroll_region(event=None):           
            canvas.after(10, lambda: canvas.configure(scrollregion=canvas.bbox("all")))

        scroll_frame.bind("<Configure>", update_scroll_region)

        # Also bind to canvas for additional updates
        canvas.bind("<Configure>", update_scroll_region)

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scrollbar.set)
       
        canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))
        h_scrollbar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        hourly_frame.grid_columnconfigure(0, weight=1)
        hourly_frame.grid_rowconfigure(1, weight=1)

        if hasattr(self, 'widgets') and self.widgets is not None:
            self.widgets['hourly_canvas'] = canvas
        # Always store as direct attribute as backup
        self.hourly_canvas = canvas

        # Create default message
        self.create_default_hourly_message()
    
    

    def get_icon_path(self, weather_main: str) -> str:
        """Get icon path with fallback"""
        return self.icon_map.get(weather_main, "icons/icons8-question-mark-50.png")

    def update_weather_display(self, weather_data: Dict, units: str = "imperial"):     
        try:
            temp = weather_data.get("temperature", "--")
            temp_unit = weather_data.get("temp_unit", "°F")
            city = weather_data.get("city", "Unknown")
            condition = weather_data.get("weather_detail", "N/A").title()
            icon_key = weather_data.get("weather_summary", "Unknown")
            icon_path = self.get_icon_path(icon_key)
         
            if self.widgets["temp_label"]:
                self.widgets["temp_label"].config(text=f"{temp}{temp_unit}")
            if self.widgets["city_label"]:
                self.widgets["city_label"].config(text=city)
            if self.widgets["desc_label"]:
                self.widgets["desc_label"].config(text=condition)
            
            if self.widgets["icon_label"] and icon_path:
                icon_img = ImageTk.PhotoImage(Image.open(icon_path).resize((50, 50)))
                self.widgets["icon_label"].config(image=icon_img)
                self.widgets["icon_label"].image = icon_img  # prevent garbage collection

            if self.widgets["details_frame"]:
                self.clear_widget("details_frame")
                details = [
                    f"Feels Like: {weather_data.get('feels_like', '--')}{temp_unit}",
                    f"Humidity: {weather_data.get('humidity', '--')}%",
                    f"Pressure: {weather_data.get('pressure', '--')} hPa",
                    f"Wind: {weather_data.get('wind_speed', '--')} m/s",
                    f"Sunrise: {weather_data.get('sunrise', '--')}",
                    f"Sunset: {weather_data.get('sunset', '--')}"
                ]
                for detail in details:
                    tk.Label(self.widgets["details_frame"], text=detail,
                            font=("Segoe UI", 10), bg="#1e40af", fg="white").pack(anchor="w", pady=2)

        except Exception as e:
            self.logger.error(f"⚠️ Weather display update failed: {e}")
  
    def get_widget(self, widget_name):    
        return self.widgets.get(widget_name)

    def clear_widget(self, widget_name):      
        widget = self.widgets.get(widget_name)
        if widget:
            for child in widget.winfo_children():
                child.destroy()
    def update_hourly_forecast(self, city, country, units):     
        try:
            scroll_frame = None
            if self.widgets and 'hourly_scroll_frame' in self.widgets and self.widgets['hourly_scroll_frame']:
                scroll_frame = self.widgets['hourly_scroll_frame']
                for widget in scroll_frame.winfo_children():
                    widget.destroy()
            elif hasattr(self, 'hourly_scroll_frame') and self.hourly_scroll_frame:
                scroll_frame = self.hourly_scroll_frame
                for widget in scroll_frame.winfo_children():
                    widget.destroy()
            else:
                self.logger.warning("hourly_scroll_frame is not set — forecast update skipped.")
                return

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
                    scroll_frame,
                    text="❌ Unable to load hourly forecast\nPlease check your internet connection",
                    font=("Segoe UI", 12),
                    bg="#f8fafc",
                    fg="#e74c3c"
                )
                error_label.pack(pady=20)
                return

            # Create horizontal container frame with uniform sizing
            container_frame = tk.Frame(scroll_frame, bg="#f8fafc")
            container_frame.pack(fill="x", expand=False, padx=5, pady=5)

            # Calculate uniform card dimensions
            num_cards = min(len(hourly_data), 8)  
            card_width = 110  
            card_height = 160  
            card_spacing = 5   
            icon_mgr = WeatherIconManager()
         
            for i, hour_data in enumerate(hourly_data[:num_cards]):
                try:                 
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
                    inner_frame.pack(fill="both", expand=True, padx=5, pady=5)
                 
                    time_display = hour_data.get('time', 'N/A')
                    time_label = tk.Label(
                        inner_frame,
                        text=time_display,
                        font=("Segoe UI", 9, "bold"),
                        bg="#4b5563",
                        fg="white"
                    )
                    time_label.pack(pady=(0, 5))

               
                    weather_main = hour_data.get("weather_main", "")
                    try:
                        icon_path = icon_mgr.get_icon_path(weather_main)
                        img = Image.open(icon_path).resize((35, 35))
                        photo = ImageTk.PhotoImage(img)
                        icon_label = tk.Label(inner_frame, image=photo, bg="#4b5563")
                        icon_label.image = photo  # Keep reference
                    except Exception as e:
                        self.logger.warning(f"[Icon Load Error] {e}")
                        emoji = WeatherEmoji.get_weather_emoji(weather_main)
                        icon_label = tk.Label(inner_frame, text=emoji, font=("Segoe UI", 18), bg="#4b5563")

                    icon_label.pack(pady=(0, 5))

                    # Weather description (centered, with text wrapping)
                    desc = hour_data.get('weather_desc', '').title()
                    if len(desc) > 12:  # Truncate long descriptions
                        desc = desc[:10] + "..."
                    desc_label = tk.Label(
                        inner_frame,
                        text=desc,
                        font=("Segoe UI", 7),
                        bg="#4b5563",
                        fg="lightgray",
                        wraplength=90,
                        justify="center"
                    )
                    desc_label.pack(pady=(0, 5))
               
                    temp = hour_data.get('temp', 0)
                    temp_label = tk.Label(
                        inner_frame,
                        text=f"{temp:.0f}°",
                        font=("Segoe UI", 11, "bold"),
                        bg="#4b5563",
                        fg="white"
                    )
                    temp_label.pack(pady=(0, 3))

                    pop = hour_data.get('pop', 0)
                    if pop > 0:
                        precip_label = tk.Label(
                            inner_frame,
                            text=f"{pop:.0f}%",
                            font=("Segoe UI", 8),
                            bg="#4b5563",
                            fg="#87ceeb"  
                        )
                        precip_label.pack()

                except Exception as hour_error:
                    self.logger.error(f"Error displaying hour {i}: {hour_error}")
                    continue

            container_frame.update_idletasks()
            scroll_frame.update_idletasks()

        except Exception as e:
            self.logger.error(f"Critical error in update_hourly_forecast: {e}")
            scroll_frame = (self.widgets.get('hourly_scroll_frame') if self.widgets and 'hourly_scroll_frame' in self.widgets 
                        else getattr(self, 'hourly_scroll_frame', None))
            if scroll_frame:
                error_label = tk.Label(
                    scroll_frame,
                    text="💥 Critical error loading hourly forecast",
                    font=("Segoe UI", 12),
                    bg="#f8fafc",
                    fg="#e74c3c"
                )
                error_label.pack(pady=20)
   