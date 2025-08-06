import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class ActivitySuggester:
    def __init__(self, temp_c: float, condition: str):
        self.temp_c = temp_c
        self.condition = condition.lower()
        self.temp_f = temp_c
        self.current_weather_data = None

    def get_suggestion(self) -> str:
        if any(word in self.condition for word in ['rain', 'drizzle', 'shower']):
            return "☔ Perfect for indoor activities - read a book, cook, or watch movies!"
        elif any(word in self.condition for word in ['snow', 'blizzard', 'ice']):
            return "❄️ Winter wonderland! Build a snowman or enjoy hot cocoa inside!"
        elif any(word in self.condition for word in ['storm', 'thunder', 'lightning']):
            return "⚡ Stay safe indoors - great time for board games or creative projects!"
        elif any(word in self.condition for word in ['fog', 'mist', 'haze']):
            return "🌫️ Limited visibility - perfect for indoor workout or meditation!"
                
        if self.temp_f < 32:
            return "🧊 Bundle up! Perfect for winter sports or cozy indoor activities!"
        elif self.temp_f < 50:
            return "🧥 Chilly day - great for brisk walks, shopping, or museum visits!"
        elif self.temp_f < 70:
            return "🍂 Perfect weather for hiking, cycling, or outdoor photography!"
        elif self.temp_f < 80:
            return "🌞 Beautiful day! Ideal for picnics, gardening, or outdoor sports!"
        elif self.temp_f < 90:
            return "🏖️ Great beach weather! Swimming, barbecue, or park activities!"
        else:
            return "🌡️ Stay cool! Early morning walks, indoor activities, or pool time!"

    def get_color(self) -> str:
        if any(word in self.condition for word in ['rain', 'storm', 'snow']):
            return "#64748b"
        elif self.temp_c < 0:
            return "#3b82f6"
        elif self.temp_c < 20:
            return "#10b981"
        elif self.temp_c < 30:
            return "#f59e0b"
        else:
            return "#ef4444"
