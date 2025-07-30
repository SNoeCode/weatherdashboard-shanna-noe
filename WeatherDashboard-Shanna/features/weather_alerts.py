import os
import tkinter as tk
import requests
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('WEATHER_API_KEY')
CITY_ID = '4634946'  
UNITS = 'imperial'  

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?id={CITY_ID}&appid={API_KEY}&units={UNITS}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        desc = data['weather'][0]['description'].title()
        temp = round(data['main']['temp'])
        city = data['name']
        weather_label.config(text=f"{city}: {temp}°F, {desc}")
    else:
        weather_label.config(text="Error fetching weather data")

root = tk.Tk()
root.title("Weather in Richmond, IN")

weather_label = tk.Label(root, font=("Helvetica", 16), padx=20, pady=20)
weather_label.pack()

refresh_button = tk.Button(root, text="Refresh", command=get_weather)
refresh_button.pack()

get_weather()
root.mainloop()