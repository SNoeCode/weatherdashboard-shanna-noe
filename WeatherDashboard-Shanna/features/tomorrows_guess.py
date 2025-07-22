import tkinter as tk
from tkinter import ttk
from weather_data_fetcher import WeatherDataFetcher as fetcher 
from weather_db import WeatherDB as db
from utils.date_time import format_local_time
from typing import List, Dict
from features.simple_statisitics import get_weather_stats
def guess_tomorrow_temp(readings):
    if len(readings) < 2:
        return "Not enough data"
    change = readings[0]['temp'] - readings[-1]['temp']
    trend = "warmer" if change < 0 else "cooler"
    return f"Tomorrow will likely be {trend} by {abs(change):.1f}°C"


class TomorrowGuessPanel:
    def __init__(self, parent_tab, db, logger, cfg):
        self.db = db
        self.logger = logger
        self.cfg = cfg
        

        self.frame = ttk.Frame(parent_tab, padding=20)
        self.frame.pack(expand=True, fill='both')

        ttk.Label(self.frame, text="🔮 Tomorrow’s Temperature Prediction", font=("Segoe UI", 16, "bold")).pack(pady=10)
        ttk.Button(self.frame, text="Guess", command=self.display_guess).pack()

    def display_guess(self):
        readings = self.db.fetch_recent("Knoxville", "US")
        prediction = guess_tomorrow_temp(readings)
        ttk.Label(self.frame, text=prediction).pack(pady=10)
        self.logger.info(f"Tomorrow's guess: {prediction}")
        