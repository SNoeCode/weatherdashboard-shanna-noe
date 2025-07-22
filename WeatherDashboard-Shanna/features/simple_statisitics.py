from collections import Counter, defaultdict
from typing import Dict
import tkinter as tk
from tkinter import ttk, messagebox
from weather_db import WeatherDB

db = WeatherDB()
def get_weather_stats(city: str, country: str) -> Dict:
    """
    Analyzes recent weather readings for a city to extract simple statistics.

    Args:
        db: Your database interface with `fetch_recent()`.
        city (str): City name.
        country (str): 2-letter country code.

    Returns:
        Dict: A dictionary with min/max temperatures and the most common weather condition.
    """
    readings = db.fetch_recent(city, country, hours=48)
    if not readings:
        return {
            "min_temp": 0.0,
            "max_temp": 0.0,
            "common_conditions": "Unknown"
        }

    temps = [r["temp"] for r in readings if r.get("temp") is not None]
    summaries = [r["weather_summary"] for r in readings if r.get("weather_summary")]

    return {
        "min_temp": min(temps) if temps else 0.0,
        "max_temp": max(temps) if temps else 0.0,
        "common_conditions": Counter(summaries).most_common(1)[0][0] if summaries else "Unknown"
    }
    
def show_statistics(frame, db, city="Knoxville", country="US"):
    readings = db.fetch_recent(city, country)
    if not readings: return

    temps = [r['temp'] for r in readings]
    conditions = [r['weather_summary'] for r in readings]

    min_temp = min(temps)
    max_temp = max(temps)
    summary = defaultdict(int)
    for cond in conditions:
        summary[cond] += 1

    stats_frame = ttk.LabelFrame(frame, text="📈 Weather Stats", padding=10)
    stats_frame.pack(pady=10, fill="x")

    ttk.Label(stats_frame, text=f"Min: {min_temp:.1f}°C").pack()
    ttk.Label(stats_frame, text=f"Max: {max_temp:.1f}°C").pack()
    for cond, count in summary.items():
        ttk.Label(stats_frame, text=f"{cond}: {count}x").pack()
        
    
def setup_stats_tab(self):
    frame = ttk.Frame(self.stats_tab, padding=20)
    frame.pack(expand=True, fill='both')

    ttk.Label(frame, text="📊 Recent Statistics", font=("Segoe UI", 16, "bold")).pack(pady=10)

    # Show stats on load
    show_statistics(frame, self.db, city="Knoxville", country="US")
