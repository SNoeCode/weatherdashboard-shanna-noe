
    
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv
from features.guessing_game import ClimateQuizGame
from config import Config


class CreateHeader:
    def __init__(self, root, get_weather_callback, toggle_theme_callback=None, refresh_callbacks=None):
        self.root = root
        self.get_weather_callback = get_weather_callback
        self.toggle_theme_callback = toggle_theme_callback
        self.refresh_callbacks = refresh_callbacks or {}
        self.create_header()
        
    def create_header(self):
        header_frame = tk.Frame(self.root, bg="#2563eb", height=80)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)

        current_time = datetime.now().strftime("%I:%M %p")
        self.time_label = tk.Label(header_frame, text=current_time,
                                   font=("Segoe UI", 24, "bold"),
                                   bg="#2563eb", fg="white")
        self.time_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        title_label = tk.Label(header_frame, text="🌤️ Weather Dashboard Pro",
                               font=("Segoe UI", 20, "bold"),
                               bg="#2563eb", fg="white")
        title_label.grid(row=0, column=1, pady=15)

        search_frame = tk.Frame(header_frame, bg="#2563eb")
        search_frame.grid(row=0, column=2, sticky="e", padx=20, pady=15)

        self.city_entry = tk.Entry(search_frame, width=15, font=("Segoe UI", 10))
        self.city_entry.grid(row=0, column=0, padx=(0, 5))
        self.city_entry.insert(0, "Knoxville")
        
        # Add Enter key binding to city entry
        self.city_entry.bind('<Return>', lambda event: self.search_and_refresh_all())

        self.country_entry = tk.Entry(search_frame, width=5, font=("Segoe UI", 10))
        self.country_entry.grid(row=0, column=1, padx=(0, 10))
        self.country_entry.insert(0, "US")
        
        # Add Enter key binding to country entry
        self.country_entry.bind('<Return>', lambda event: self.search_and_refresh_all())

        # FIXED: Changed command to call search_and_refresh_all instead of get_weather_callback directly
        search_btn = tk.Button(search_frame, text="🔍", font=("Segoe UI", 12),
                               bg="#1d4ed8", fg="white", cursor="hand2",
                               command=self.search_and_refresh_all)  # <-- This was the fix!
        search_btn.grid(row=0, column=2, padx=2)

        game_btn = tk.Button(search_frame, text="🎮 Play Now", font=("Segoe UI", 10),
                    bg="#16a34a", fg="white", cursor="hand2",
                    command=self.open_game_popup)
        game_btn.grid(row=0, column=4, padx=5)
        
        self.update_time()

    def search_and_refresh_all(self):
        """Main method that handles searching and refreshing all components"""
        city = self.get_city()
        country = self.country_entry.get().strip() or "US"
        
        print(f"DEBUG: Searching for weather in {city}, {country}")  # Debug output
        
        # Call the original weather callback first with the new city/country
        if self.get_weather_callback:
            try:
                # Pass city and country to the weather callback
                self.get_weather_callback(city, country)
                print(f"DEBUG: Weather callback executed for {city}, {country}")
            except Exception as e:
                print(f"ERROR: Weather callback failed: {e}")
                # Try without parameters as fallback
                try:
                    self.get_weather_callback()
                except Exception as e2:
                    print(f"ERROR: Weather callback fallback also failed: {e2}")
        
        # Refresh all registered components with the new location
        for callback_name, callback_func in self.refresh_callbacks.items():
            try:
                if callback_func:
                    print(f"DEBUG: Refreshing {callback_name} for {city}, {country}")
                    callback_func(city, country)
            except Exception as e:
                print(f"ERROR: Failed to refresh {callback_name}: {e}")

    def register_refresh_callback(self, name, callback):
        """Register a callback for refreshing components when location changes"""
        self.refresh_callbacks[name] = callback
        print(f"DEBUG: Registered refresh callback '{name}'")
    
    def open_game_popup(self):
        ClimateQuizGame(self.root)

    def update_time(self):
        if self.root.winfo_exists(): 
            current_time = datetime.now().strftime("%I:%M %p")
            self.time_label.config(text=current_time)
            self.root.after(60000, self.update_time)
     
    def get_city(self):    
        return self.city_entry.get().strip() or "Knoxville"
    
    def get_location(self):
        return self.city_entry.get().strip() or "Knoxville", self.country_entry.get().strip() or "US"