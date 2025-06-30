import tkinter as tk
import requests
import os
from dotenv import load_dotenv

load_dotenv()



class WeatherApp:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.root = tk.Tk()
        self.root.title("Weather App")
        self.root.geometry("400x300")

        self.city_entry = tk.Entry(self.root, width=25)
        self.city_entry.pack(pady=10)

        self.button = tk.Button(self.root, text="Get Weather", command=self.get_weather)
        self.button.pack()

        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack(pady=20)

    def get_weather(self):
        city = self.city_entry.get()
        if city:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=imperial"
            try:
                response = requests.get(url, timeout=10)
                data = response.json()
                if response.status_code == 200:
                    temp = data['main']['temp']
                    desc = data['weather'][0]['description']
                    self.result_label.config(text=f"{city}: {temp}°F, {desc.title()}")
                else:
                    self.result_label.config(text="City not found.")
            except Exception as e:
                self.result_label.config(text=str(e))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = WeatherApp()
    app.run()