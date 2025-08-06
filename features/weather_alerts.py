import os
import tkinter as tk
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('WEATHER_API_KEY')
UNITS = 'imperial'

def get_coordinates(city_name):
    geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"
    response = requests.get(geo_url)
    if response.status_code == 200:
        results = response.json()
        if results:
            return results[0]['lat'], results[0]['lon'], results[0]['name']
    return None, None, "Location not found"

def get_weather(city_name):
    lat, lon, display_name = get_coordinates(city_name)
    if lat is None or lon is None:
        weather_label.config(text="Invalid location. Try again.")
        alert_label.config(text="")
        return

    weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={API_KEY}&units={UNITS}"
    response = requests.get(weather_url)

    if response.status_code == 200:
        data = response.json()

        # Current weather
        current = data['current']
        desc = current['weather'][0]['description'].title()
        temp = round(current['temp'])
        weather_label.config(text=f"{display_name}: {temp}°F, {desc}")

        # Alerts
        if 'alerts' in data:
            alerts = data['alerts']
            alert_messages = [f"⚠️ {a['event']}: {a['description']}" for a in alerts]
            alerts_text = "\n\n".join(alert_messages)
        else:
            alerts_text = "✅ No active alerts at the moment."

        alert_label.config(text=alerts_text)

    else:
        weather_label.config(text="Error fetching weather data")
        alert_label.config(text="")

def refresh_weather():
    city_name = city_entry.get().strip()
    if not city_name:
        city_name = "Knoxville, TN"
    get_weather(city_name)

root = tk.Tk()
root.title("Dynamic Weather & Alerts Dashboard")

# Entry field for location
city_entry = tk.Entry(root, font=("Helvetica", 12), width=30)
city_entry.insert(0, "Knoxville, TN")
city_entry.pack(pady=(10, 0))

search_button = tk.Button(root, text="Search", command=refresh_weather, font=("Helvetica", 12))
search_button.pack(pady=5)

weather_label = tk.Label(root, font=("Helvetica", 16), padx=20, pady=10)
weather_label.pack()

alert_label = tk.Label(root, font=("Helvetica", 12), fg="red", wraplength=500, justify="left", padx=20, pady=10)
alert_label.pack()

refresh_weather()
root.mainloop()