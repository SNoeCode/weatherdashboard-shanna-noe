from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from config import Config
config = Config.load_from_env()
from typing import cast
icon_map = {
    "Clear": "icons/icons8-sun-50.png",
    "Rain": "icons/icons8-rain-50.png",
    "Thunderstorm": "icons/icons8-thunderstorm-100.png",
    "Clouds": "icons/icons8-clouds-50.png",
    "Snow": "icons/icons8-snow-50.png",
    "Wind": "icons/icons8-windy-weather-50.png", 
    "Mist": "icons/weather_icons_dovora_interactive/PNG/128/mist.png"
}

def fade_in(widget, delay=30, steps=10):
    """Gradually changes widget foreground color from light gray to black."""
    def step(opacity):
        level = int(255 * opacity)
        color = f"#{level:02x}{level:02x}{level:02x}"
        widget.config(foreground=color)
        if opacity < 1:
            widget.after(delay, step, opacity + 1 / steps)
    step(0)
    
def get_icon_path(weather_main: str) -> str:
    return icon_map.get(weather_main, "icons/icons8-question-mark-50.png")

    
def display_weather_with_icon(weather_frame, weather_data, fetcher, render_forecast):
    for widget in weather_frame.winfo_children():
        widget.destroy()

    #Convert metric to Fahrenheit
    temp = (weather_data["temp"] * 9 / 5) + 32 if weather_data["country"] == "US" else weather_data["temp"]
    unit = "°F" if weather_data["country"] == "US" else "°C"

    #Fetch weather icon path
    weather_main = weather_data.get("weather_summary", "Unknown")
    icon_path = get_icon_path(weather_main)

    try:
        img = Image.open(icon_path).resize((64, 64))
        photo = ImageTk.PhotoImage(img)
        icon_label = tk.Label(weather_frame, image=photo, bg="#f0f8ff")
        icon_label.image = photo   # type: ignore
        icon_label.pack(anchor="center", pady=5)
    except Exception as e:
        print(f"[Icon Error] {e}")

    #Temperature label
    temp_label = ttk.Label(weather_frame, text=f"{temp:.1f}{unit}", font=("Segoe UI", 24, "bold"), foreground="#888")
    temp_label.pack(anchor="center")
    fade_in(temp_label)

    #Description label
    desc = f"{weather_data['city']}, {weather_data['country']} — {weather_data['weather_detail'].capitalize()}"
    desc_label = ttk.Label(weather_frame, text=desc, font=("Segoe UI", 12), foreground="#888")
    desc_label.pack(anchor="center")
    fade_in(desc_label)

    #Forecast render
    forecast = fetcher.fetch_five_day_forecast(weather_data["city"], weather_data["country"])
    if forecast:
        render_forecast(weather_frame, forecast, weather_data["country"])

