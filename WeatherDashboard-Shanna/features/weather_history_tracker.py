import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import Image, ImageTk
from datetime import datetime
from features.weather_icons import get_icon_path  # ✅ No need to import display_weather_with_icon here
from typing import Dict, Optional  

def render_five_day_forecast(parent, forecast_data, country="US"):
    frame = ttk.LabelFrame(parent, text="5-Day Forecast", padding=10)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    #Group entries by date
    daily = defaultdict(list)
    for entry in forecast_data.get("list", []):
        date_str = entry["dt_txt"].split(" ")[0]  # YYYY-MM-DD
        daily[date_str].append(entry)

    #Display one card per day (limit to next 5 days)
    for i, (date, entries) in enumerate(daily.items()):
        if i >= 5:
            break

        #Use midday forecast if available, else first
        midday = next((e for e in entries if "12:00:00" in e["dt_txt"]), entries[0])
        temp_c = midday["main"]["temp"]
        summary = midday["weather"][0]["main"]
        desc = midday["weather"][0]["description"]
        icon_path = get_icon_path(summary)

        temp = (temp_c * 9 / 5) + 32 if country == "US" else temp_c
        unit = "°F" if country == "US" else "°C"
        date_formatted = datetime.strptime(date, "%Y-%m-%d").strftime("%A\n%b %d")

        card = ttk.Frame(frame, width=120)
        card.pack(side="left", padx=10)

        try:
            img = Image.open(icon_path).resize((48, 48))
            photo = ImageTk.PhotoImage(img)
            icon = tk.Label(card, image=photo)
            icon.image = photo  #type: ignore
            icon.pack()
        except Exception as e:
            print(f"[Icon Error] {e}")

        ttk.Label(card, text=date_formatted, font=("Segoe UI", 9, "bold")).pack()
        ttk.Label(card, text=f"{temp:.1f}{unit}", font=("Segoe UI", 9)).pack()
        ttk.Label(card, text=desc.capitalize(), font=("Segoe UI", 9)).pack()



# def render_seven_day_forecast(parent, forecast_data, country="US"):
#     frame = ttk.LabelFrame(parent, text="7-Day Forecast", padding=10)
#     frame.pack(fill="both", expand=True, padx=10, pady=10)

#     for day in forecast_data.get("daily", [])[1:8]:  # Skip today's forecast
#         date_str = datetime.fromtimestamp(day["dt"]).strftime("%A\n%b %d")
#         temp_c = day["temp"]["day"]
#         desc = day["weather"][0]["description"]
#         summary = day["weather"][0]["main"]
#         temp = (temp_c * 9 / 5) + 32 if country == "US" else temp_c
#         unit = "°F" if country == "US" else "°C"

#         icon_path = get_icon_path(summary)

#         card = ttk.Frame(frame, width=120)
#         card.pack(side="left", padx=10)

#         try:
#             img = Image.open(icon_path).resize((48, 48))
#             photo = ImageTk.PhotoImage(img)
#             icon = tk.Label(card, image=photo)
#             icon.image = photo    # type: ignore
#             icon.pack()
#         except Exception as e:
#             print(f"[Icon Error] {e}")

#         ttk.Label(card, text=date_str, font=("Segoe UI", 9, "bold")).pack()
#         ttk.Label(card, text=f"{temp:.1f}{unit}", font=("Segoe UI", 9)).pack()
#         ttk.Label(card, text=desc.capitalize(), font=("Segoe UI", 9)).pack()