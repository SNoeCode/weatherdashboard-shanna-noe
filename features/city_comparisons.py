import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from features.simple_statistics import SimpleStatsPanel
from services.weather_stats import get_weather_stats
from datetime import datetime
import threading
from weather_db import WeatherDB
from weather_data_fetcher import WeatherDataFetcher
from typing import Dict, List
from config import Config 
from features.weather_icons import WeatherIconManager
class CityComparisonPanel:
    def __init__(self, parent_tab, fetcher, db, logger):
        self.fetcher = fetcher
        self.db = db
        self.logger = logger
        self.comparison_data = {}
        self.main_frame = ttk.Frame(parent_tab, padding=25)
        self.main_frame.pack(expand=True, fill='both')

        self.create_header()
        self.create_input_section()
        self.create_comparison_display()
        self.create_detailed_comparison()

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill='x', pady=(0, 25))

        ttk.Label(header_frame, text="🆚 City Weather Comparison", font=("Segoe UI", 22, "bold")).pack(pady=(0, 5))
        ttk.Label(header_frame, text="Compare current weather conditions and statistics between two cities",
                  font=("Segoe UI", 12), foreground="#666666").pack()

    def create_input_section(self):
        input_frame = ttk.LabelFrame(self.main_frame, text="🌍 Select Cities to Compare", padding=20)
        input_frame.pack(fill='x', pady=(0, 25))

        grid_frame = ttk.Frame(input_frame)
        grid_frame.pack(expand=True)

        city_a_frame = ttk.LabelFrame(grid_frame, text="🌆 City A", padding=15)
        city_a_frame.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        ttk.Label(city_a_frame, text="City Name:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        self.city1_entry = ttk.Entry(city_a_frame, width=25, font=("Segoe UI", 11))
        self.city1_entry.pack(fill='x', pady=(2, 10))
        self.city1_entry.insert(0, "Knoxville")
        ttk.Label(city_a_frame, text="Country Code:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        self.country1_entry = ttk.Entry(city_a_frame, width=25, font=("Segoe UI", 11))
        self.country1_entry.pack(fill='x', pady=(2, 0))
        self.country1_entry.insert(0, "US")

        vs_frame = ttk.Frame(grid_frame)
        vs_frame.grid(row=0, column=1, padx=15)
        ttk.Label(vs_frame, text="VS", font=("Segoe UI", 20, "bold"), foreground="#FF6B6B").pack(pady=40)

        city_b_frame = ttk.LabelFrame(grid_frame, text="🏙️ City B", padding=15)
        city_b_frame.grid(row=0, column=2, padx=(15, 0), sticky="nsew")
        ttk.Label(city_b_frame, text="City Name:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        self.city2_entry = ttk.Entry(city_b_frame, width=25, font=("Segoe UI", 11))
        self.city2_entry.pack(fill='x', pady=(2, 10))
        self.city2_entry.insert(0, "Nashville")
        ttk.Label(city_b_frame, text="Country Code:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        self.country2_entry = ttk.Entry(city_b_frame, width=25, font=("Segoe UI", 11))
        self.country2_entry.pack(fill='x', pady=(2, 0))
        self.country2_entry.insert(0, "US")

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(2, weight=1)

        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill='x', pady=(20, 0))

        self.compare_button = ttk.Button(button_frame, text="🔍 Compare Cities", command=self.compare_cities_threaded, style="Accent.TButton")
        self.compare_button.pack(expand=True)

        self.loading_label = ttk.Label(button_frame, text="", font=("Segoe UI", 10))
        self.loading_label.pack(pady=(10, 0))

    def create_comparison_display(self):
        self.comparison_frame = ttk.LabelFrame(self.main_frame, text="📊 Weather Comparison", padding=20)
        self.comparison_frame.pack(fill='both', expand=True, pady=(0, 20))
        self.show_welcome_message()

    def create_detailed_comparison(self):
        self.details_frame = ttk.LabelFrame(self.main_frame, text="📋 Detailed Analysis", 
                                        padding=40, height=200, width=600)
        self.details_frame.pack(fill='both', expand=True, pady=(10, 0))
        self.main_frame.update() 
        self.details_frame.configure(height=250)
        self.details_frame.pack_forget()
        self.details_frame.pack_propagate(False)

    def show_welcome_message(self):
        welcome_frame = ttk.Frame(self.comparison_frame)
        welcome_frame.pack(expand=True, fill='both')
        ttk.Label(welcome_frame, text="🌤️", font=("Segoe UI", 72)).pack(pady=(50, 20))
        ttk.Label(welcome_frame, text="Ready to Compare Cities", font=("Segoe UI", 18, "bold")).pack()
        ttk.Label(welcome_frame,
                  text="Enter two cities above and click 'Compare Cities' to see the weather comparison",
                  font=("Segoe UI", 11), foreground="#666666").pack(pady=(10, 0))

    def compare_cities_threaded(self):
        threading.Thread(target=self.compare_cities, daemon=True).start()

    def compare_cities(self):
        self.root_after_idle(self.show_loading)

        city_a = self.city1_entry.get().strip()
        city_b = self.city2_entry.get().strip()
        country_a = self.country1_entry.get().strip() or "US"
        country_b = self.country2_entry.get().strip() or "US"
        
        # FIX: Always use imperial units for US cities, metric for others
        units_a = "imperial" if country_a.upper() == "US" else "metric"
        units_b = "imperial" if country_b.upper() == "US" else "metric"
        
        if not city_a or not city_b:
            self.root_after_idle(lambda: messagebox.showwarning("Missing Input", "Please enter both cities."))
            self.root_after_idle(self.hide_loading)
            return

        try:
         
            data_a = self.fetcher.fetch_current_weather(city_a, country_a, units_a)
            data_b = self.fetcher.fetch_current_weather(city_b, country_b, units_b)

            if not data_a or not data_b:
                self.root_after_idle(lambda: messagebox.showerror("❌ Compare Error", "Could not fetch weather for one or both cities."))
                self.root_after_idle(self.hide_loading)
                return

            city_a_name = data_a.get("city") or data_a.get("name")
            country_a_code = data_a.get("country") or data_a.get("sys", {}).get("country")

            city_b_name = data_b.get("city") or data_b.get("name")
            country_b_code = data_b.get("country") or data_b.get("sys", {}).get("country")
   
            stats_a = get_weather_stats(self.db, city_a_name, country_a_code)
            stats_b = get_weather_stats(self.db, city_b_name, country_b_code)

            self.comparison_data = {
                'city_a': {'data': data_a, 'stats': stats_a},
                'city_b': {'data': data_b, 'stats': stats_b}
            }

            self.root_after_idle(self.display_comparison_results)

        except Exception as e:
            self.logger.error(f"Error in city comparison: {e}")
            self.root_after_idle(lambda err=e: messagebox.showerror("Error", f"Comparison failed: {str(err)}"))
            self.root_after_idle(self.hide_loading)

    def root_after_idle(self, func):
        self.main_frame.after_idle(func)

    def show_loading(self):
        self.compare_button.config(state='disabled')
        self.loading_label.config(text="🔄 Fetching weather data...")

        for widget in self.comparison_frame.winfo_children():
            widget.destroy()

        loading_frame = ttk.Frame(self.comparison_frame)
        loading_frame.pack(expand=True, fill='both')
        ttk.Label(loading_frame, text="🔄", font=("Segoe UI", 48)).pack(pady=(50, 10))
        ttk.Label(loading_frame, text="Loading Comparison...", font=("Segoe UI", 14, "bold")).pack()

    def hide_loading(self):
        self.compare_button.config(state='normal')
        self.loading_label.config(text="")

    def display_comparison_results(self):
        self.hide_loading()
        for widget in self.comparison_frame.winfo_children():
            widget.destroy()

        if not self.comparison_data:
            return

        container = ttk.Frame(self.comparison_frame)
        container.pack(expand=True, fill='both')

        self.create_city_card(container, self.comparison_data['city_a'], "City A", 0)
        self.create_comparison_indicators(container)
        self.create_city_card(container, self.comparison_data['city_b'], "City B", 2)

        container.columnconfigure(0, weight=1)
        container.columnconfigure(2, weight=1)

        self.show_detailed_comparison()

    def create_city_card(self, container, city_data, label, column):
        frame = ttk.Frame(container, padding=10)
        frame.grid(row=0, column=column, sticky="nsew")

        name = city_data["data"].get("city", "Unknown")
        temp = city_data["data"].get("temperature", "N/A")
        unit = city_data["data"].get("temp_unit", "°C")
        
        condition = (city_data["data"].get("weather_summary", "") or 
                    city_data["data"].get("condition", "") or 
                    city_data["data"].get("weather_main", "Clear"))

        # Create labels
        ttk.Label(frame, text=f"{name}", font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))
        ttk.Label(frame, text=f"{temp}{unit}", font=("Segoe UI", 20)).pack(pady=5)
        ttk.Label(frame, text=condition.title(), font=("Segoe UI", 12)).pack()

        try:
            icon_mgr = WeatherIconManager()
            icon_path = icon_mgr.get_icon_path(condition)
            print(f"Loading icon: {icon_path} for condition: {condition}")  # Debug
            
            img = Image.open(icon_path).resize((64, 64))
            photo = ImageTk.PhotoImage(img)
            icon_label = ttk.Label(frame, image=photo)
            icon_label.image = photo  # type:ignore
            icon_label.pack(pady=5)
        except Exception as e:
            print(f"[Icon Error] {e}")
            ttk.Label(frame, text="🌤️", font=("Segoe UI", 32)).pack(pady=5)
                
    def create_comparison_indicators(self, container):
        indicator_frame = ttk.Frame(container, padding=10)
        indicator_frame.grid(row=0, column=1, sticky="nsew")

        temp_a = self.comparison_data["city_a"]["data"].get("temperature", 0)
        temp_b = self.comparison_data["city_b"]["data"].get("temperature", 0)

        unit_a = self.comparison_data["city_a"]["data"].get("temp_unit", "°C")
        unit_b = self.comparison_data["city_b"]["data"].get("temp_unit", "°C")
        
        try:
            diff = round(abs(float(temp_a) - float(temp_b)), 1)
            unit_label = unit_a if unit_a == unit_b else f"{unit_a.replace('°', '')}"
            msg = f"🌡️ Temperature Difference: {diff}°{unit_label.replace('°', '')}"
        except Exception:
            msg = "🌡️ Temperature Difference: N/A"

        ttk.Label(indicator_frame, text=msg, font=("Segoe UI", 12, "bold"), foreground="#FF6B6B").pack(pady=30)

    def show_detailed_comparison(self):
        self.details_frame.pack(fill='both', expand=True, pady=(10, 0))

        for widget in self.details_frame.winfo_children():
            widget.destroy()

        stats_a = self.comparison_data['city_a']['stats']
        stats_b = self.comparison_data['city_b']['stats']

   
        country_a = self.comparison_data['city_a']['data'].get('country', 'US')
        country_b = self.comparison_data['city_b']['data'].get('country', 'US')
        
        keys = ["avg_temp", "humidity_avg", "wind_avg"]
        labels = {
            "avg_temp": f"🌡️ Avg Temp ({'°F' if country_a == 'US' else '°C'} vs {'°F' if country_b == 'US' else '°C'})",
            "humidity_avg": "💧 Avg Humidity (%)",
            "wind_avg": "🌬️ Avg Wind Speed (km/h)"
        }

        for key in keys:
            val_a = stats_a.get(key, "N/A")
            val_b = stats_b.get(key, "N/A")
            summary = f"{labels[key]}: {val_a} vs {val_b}"
            ttk.Label(self.details_frame, text=summary, font=("Segoe UI", 11)).pack(anchor='w', pady=2)

        ttk.Separator(self.details_frame, orient='horizontal').pack(fill='x', pady=(10, 10))

        timestamp = datetime.now().strftime("%A, %B %d • %I:%M %p")
        ttk.Label(self.details_frame,
                  text=f"Last compared on: {timestamp}",
                  font=("Segoe UI", 9),
                  foreground="#999999").pack(anchor='e', pady=(0, 5))