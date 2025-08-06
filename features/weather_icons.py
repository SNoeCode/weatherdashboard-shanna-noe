from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from config import Config
config = Config.load_from_env()
from typing import cast
class WeatherIconManager:
    def __init__(self):
        self.icon_map = {
            "Clear": "icons/icons8-sun-50.png",
            "Rain": "icons/icons8-rain-50.png",
            "Thunderstorm": "icons/icons8-thunderstorm-100.png",
            "Clouds": "icons/icons8-clouds-50.png",
            "Snow": "icons/icons8-snow-50.png",
            "Wind": "icons/icons8-windy-weather-50.png",
            "Mist": "icons/weather_icons_dovora_interactive/PNG/128/mist.png"
        }

    def get_icon_path(self, condition: str) -> str:
        return self.icon_map.get(condition, "icons/icons8-question-mark-50.png")

    def create_icon_label(self, parent, condition: str, size=(64, 64), **kwargs):
        path = self.get_icon_path(condition)
        try:
            img = Image.open(path).resize(size)
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(parent, image=photo, **kwargs)
            label.image = photo
            return label
        except Exception as e:
            print(f"[Icon Error] {e}")
            return tk.Label(parent, text="?", **kwargs)
