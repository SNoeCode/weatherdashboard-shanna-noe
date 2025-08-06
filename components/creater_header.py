
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv
from features.guessing_game import ClimateQuizGame
from config import Config


class CreateHeader:
    def __init__(self, root, get_weather_callback, toggle_theme_callback=None):
        self.root = root
        self.get_weather_callback = get_weather_callback
        self.toggle_theme_callback = toggle_theme_callback
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

        self.country_entry = tk.Entry(search_frame, width=5, font=("Segoe UI", 10))
        self.country_entry.grid(row=0, column=1, padx=(0, 10))
        self.country_entry.insert(0, "US")

        search_btn = tk.Button(search_frame, text="🔍", font=("Segoe UI", 12),
                               bg="#1d4ed8", fg="white", cursor="hand2",
                               command=self.get_weather_callback)
        search_btn.grid(row=0, column=2, padx=2)

        game_btn = tk.Button(search_frame, text="🎮 Play Now", font=("Segoe UI", 10),
                    bg="#16a34a", fg="white", cursor="hand2",
                    command=self.open_game_popup)
        game_btn.grid(row=0, column=4, padx=5)
        
        self.update_time()
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
        return self.city_entry.get(), self.country_entry.get()

    