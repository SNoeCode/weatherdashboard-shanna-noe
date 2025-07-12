from collections import defaultdict
import datetime
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
from dotenv import load_dotenv
from config import setup_logger
from config import Config
config = Config.load_from_env()
from typing import cast

load_dotenv()

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
    """
    Gradually changes widget foreground color from light gray to black.
    """
    def step(opacity):
        level = int(255 * opacity)
        color = f"#{level:02x}{level:02x}{level:02x}"
        widget.config(foreground=color)
        if opacity < 1:
            widget.after(delay, step, opacity + 1 / steps)
    step(0)


class WeatherAppGUI:
    def __init__(self, fetcher, db, tracker, logger):
        #Store core components (weather fetcher, database, automated tracker, logger)
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger

        #Create main window with defined size and background
        self.root = tk.Tk()
        self.root.title("🌤️ Weather Dashboard")  # Appears on the app window
        self.root.geometry("1000x700")          # Width x Height — large enough to show forecasts
        self.root.configure(bg="#f0f8ff")       # Gentle blue tone background

        #Style setup using ttk (makes buttons, labels, frames visually consistent)
        style = ttk.Style()
        style.theme_use("clam")  #Mild theme with high readability

        #Improved color palette for buttons and labels
        style.configure("TButton", font=("Segoe UI", 10, "bold"), foreground="#ffffff", background="#006699")  # Deeper blue
        style.map("TButton", foreground=[('active', '#ffffff')], background=[('active', '#004466')])
        style.configure("TLabel", background="#f7fbff", font=("Segoe UI", 11), foreground="#333")
        style.configure("TLabelframe.Label", font=("Segoe UI", 12, "bold"), foreground="#004080")
        style.configure("TLabelframe", background="#f7fbff", bordercolor="#3399ff")

        #Update root background to match
        self.root.configure(bg="#f7fbff")  #Subtle off-white
        
        #Create tab structure for switching views (Home vs Favorites)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')  #Uses full available space

        #Home tab: current weather and search
        self.home_tab = ttk.Frame(self.notebook)
        #Favorites tab: saved locations with live summary
        self.favorites_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.home_tab, text="🏠 Home")
        self.notebook.add(self.favorites_tab, text="🌍 Favorites")

        #Build contents of each tab
        self.setup_home_tab()
        self.setup_favorites_tab()

    def setup_home_tab(self):
        #Container frame for layout and padding
        frame = ttk.Frame(self.home_tab, padding=20)
        frame.pack(expand=True)

        #Search title
        title = ttk.Label(frame, text="🔎 Search Weather", font=("Segoe UI", 18, "bold"))
        title.grid(row=0, column=0, columnspan=4, pady=10)

        #City input
        ttk.Label(frame, text="City:").grid(row=1, column=0, sticky="e")
        self.city_entry = ttk.Entry(frame, width=25)
        self.city_entry.grid(row=1, column=1, padx=5)
        self.city_entry.insert(0, "Knoxville")  # Default pre-filled

        #Country input
        ttk.Label(frame, text="Country:").grid(row=1, column=2, sticky="e")
        self.country_entry = ttk.Entry(frame, width=10)
        self.country_entry.grid(row=1, column=3, padx=5)
        self.country_entry.insert(0, "US")  # Default country

        #Search button to trigger weather fetch
        self.search_button = ttk.Button(frame, text="Get Weather", command=self.get_weather_threaded)
        self.search_button.grid(row=1, column=4, padx=10)

        #Weather display box
        self.weather_frame = ttk.LabelFrame(frame, text="Current Weather", padding=10)
        self.weather_frame.grid(row=2, column=0, columnspan=5, pady=20, sticky="ew")
        self.weather_frame.columnconfigure(0, weight=1)
        self.view_mode = tk.StringVar(value="current")
        # 🌥️ Forecast Toggle (Row 3)
        self.view_mode = tk.StringVar(value="current")
        ttk.Radiobutton(frame, text="🌤️ Now", variable=self.view_mode, value="current").grid(row=3, column=0, padx=5, pady=5)
        # ttk.Radiobutton(frame, text="📆 5-Day", variable=self.view_mode, value="forecast").grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(frame, text="⭐ Save to Favorites", command=self.add_to_favorites).grid(row=5, column=0, columnspan=5, pady=10)
        #CSV Export button for saving readings
        ttk.Button(frame, text="💾 Save All to CSV", command=self.save_to_csv).grid(row=3, column=0, columnspan=5, pady=10)

    def setup_favorites_tab(self):
        #Build favorites dashboard
        frame = ttk.Frame(self.favorites_tab, padding=20)
        frame.pack(expand=True, fill='both')

        #Title
        title = ttk.Label(frame, text="🌍 Favorite Cities Dashboard", font=("Segoe UI", 18, "bold"))
        title.pack(pady=10)

        #Output Text Widget for summaries
        self.favorites_display = tk.Text(frame, height=20, width=80, wrap=tk.WORD, bg="#e6f7ff", fg="#000066")
        self.favorites_display.pack(expand=True)

        #Button to refresh readings
        ttk.Button(frame, text="🔄 Refresh", command=self.refresh_favorites).pack(pady=10)

    def refresh_favorites(self):
        #Clears and reloads favorite city weather blocks
        self.favorites_display.delete(1.0, tk.END)
        locations = self.tracker.get_active_locations()

        #Pull data from DB for each location
        with self.db.get_connection() as conn:
            for loc in locations:
                city, country, loc_id = loc["city"], loc["country"], loc["id"]

                #Get latest weather row
                latest = conn.execute("""SELECT temp, weather_detail, humidity, wind_speed, pressure, timestamp
                                         FROM readings WHERE city = ? AND country = ?
                                         ORDER BY timestamp DESC LIMIT 1""", (city, country)).fetchone()

                #Get API success history
                logs = conn.execute("""SELECT status, COUNT(*) FROM request_log
                                       WHERE location_id = ? AND timestamp > datetime('now', '-24 hours')
                                       GROUP BY status""", (loc_id,)).fetchall()

                status_counts = {row["status"]: row["COUNT(*)"] for row in logs}
                success = status_counts.get("success", 0)
                errors = sum(c for s, c in status_counts.items() if s != "success")
                total = success + errors
                rate = f"{(success / total * 100):.1f}%" if total else "N/A"

                #Output formatting
                self.favorites_display.insert(tk.END, f"📍 {city}, {country}\n", "title")

                if latest:
                    temp_f = (latest["temp"] * 9/5) + 32
                    desc = latest["weather_detail"].capitalize()
                    self.favorites_display.insert(tk.END, f"  {temp_f:.1f}°F — {desc}\n")
                    self.favorites_display.insert(tk.END, f"  Humidity: {latest['humidity']}%   Wind: {latest['wind_speed']} m/s   Pressure: {latest['pressure']} hPa\n")
                    self.favorites_display.insert(tk.END, f"  Last Reading: {latest['timestamp']}\n")
                else:
                    self.favorites_display.insert(tk.END, "  ❌ No weather data found\n")

                self.favorites_display.insert(tk.END, f"  API Success Rate: {rate}   Errors: {errors}\n\n")

        #Stylize header text in output
        self.favorites_display.tag_config("title", foreground="#0059b3", font=("Segoe UI", 12, "bold"))

    def get_weather_threaded(self):
        #Spawn a background thread to fetch weather data
        #Prevents UI freezing while waiting on API response
        threading.Thread(target=self.get_weather, daemon=True).start()

    def get_weather(self):
        #Triggered by "Get Weather" button — performs fetch + display logic
        city = self.city_entry.get().strip()
        country = self.country_entry.get().strip() or None  # Default to None if blank
        self.city_entry.delete(0, tk.END)
        self.country_entry.delete(0, tk.END)

        #Guard clause to ensure input is valid
        if not city:
            messagebox.showwarning("Missing Input", "Please enter a city name.")
            return

          #Clear inputs only after validation passes
        self.city_entry.delete(0, tk.END)
        self.country_entry.delete(0, tk.END)
    
            
        #Request current weather from the fetcher (API interface)
        result = self.fetcher.fetch_current_weather(city, country)
        
        #Clear previous GUI weather widgets so new data shows cleanly
        for widget in self.weather_frame.winfo_children():
            widget.destroy()

        #If data was retrieved, log + display it
        if result:
            self.db.insert_reading(result)
            self.tracker.database.log_request("manual_search", None, "success")
            
            
            if self.view_mode.get() == "current":
                self.display_weather_with_icon(result)
            else:
                forecast = self.fetcher.fetch_five_day_forecast(city, country)
                if forecast:
                    self.render_forecast(forecast)        
       
    def add_to_favorites(self):
        #Add current city to favorites (tracked in DB + dashboard)
        city = self.city_entry.get().strip()
        country = self.country_entry.get().strip()

        if city:
            added = self.tracker.add_location(city, country or "US")
            if added:
                messagebox.showinfo("⭐ Saved", f"{city}, {country} added to favorites.")
                self.refresh_favorites()  # Update dashboard with new city
            else:
                messagebox.showwarning("⚠️ Error", "Could not add city to favorites.")
        else:
            messagebox.showwarning("❗ Missing City", "Enter a city before adding to favorites.")
            
    def display_weather_with_icon(self, weather_data):
        #Clear previous display widgets (if user searched again)
        for widget in self.weather_frame.winfo_children():
            widget.destroy()

        #Convert metric to Fahrenheit for display
        if weather_data["country"] == "US":
            temp = (weather_data["temp"] * 9 / 5) + 32
            unit = "°F"
        else:
            temp = weather_data["temp"]
            unit = "°C"

        #Fetch weather icon path using the summary (e.g. "Rain", "Clouds")
        weather_main = weather_data['weather_summary']
        icon_path = icon_map.get(weather_main, "icons/icons8-question-mark-50.png")  # default if missing

        #Display weather icon
        try:
            img = Image.open(icon_path).resize((64, 64))  # Resize for consistency
            photo = ImageTk.PhotoImage(img)
            icon_label = tk.Label(self.weather_frame, image=photo, bg="#f0f8ff")
            icon_label.image = photo  # type: ignore
            icon_label.pack(anchor="center", pady=5)
        except Exception as e:
            print(f"[Icon Error] {e}")  
            
            
        #Show temperature label with fade-in effect
        temp_label = ttk.Label(
            self.weather_frame,
            text=f"{temp:.1f}{unit}",
            font=("Segoe UI", 24, "bold"),
            foreground="#888"
        )
        temp_label.pack(anchor="center")
        fade_in(temp_label)


        #Show weather description (e.g. "Partly cloudy", "Thunderstorm")
        desc_text = f"{weather_data['city']}, {weather_data['country']} — {weather_data['weather_detail'].capitalize()}"
        desc_label = ttk.Label(self.weather_frame, text=desc_text, font=("Segoe UI", 12), foreground="#888")
        desc_label.pack(anchor="center")
        fade_in(desc_label)

        #Fetch and render 5-day forecast for this location
        forecast = self.fetcher.fetch_five_day_forecast(weather_data["city"], weather_data["country"])
        if forecast:
            self.render_forecast(forecast)

    def render_forecast(self, forecast_data):
            #Remove old forecast frame if re-rendering
        if hasattr(self, "forecast_frame"):
            self.forecast_frame.destroy()

        #Create a container frame for the forecast section
        self.forecast_frame = ttk.LabelFrame(self.weather_frame, text="5-Day Forecast", padding=10)
        self.forecast_frame.pack(fill="both", expand=True, padx=10, pady=10)

        grouped = defaultdict(list)

        #Group forecast entries by date from 3-hour blocks
        for entry in forecast_data["list"]:
            date = entry["dt_txt"].split(" ")[0]  # Extract just the date
            grouped[date].append(entry)

        #Show forecast for up to 5 days
        for date, items in list(grouped.items())[:5]:
            day = items[len(items)//2]  # Use the middle block (around midday)

            #Extract main attributes
            temp_c = day["main"]["temp"]
            summary = day["weather"][0]["main"]
            detail = day["weather"][0]["description"]
            country = forecast_data.get("city", {}).get("country", "US")  # ⬅️ This gives us the country for unit decision

            #Convert temperature based on country
            if country == "US":
                temp = (temp_c * 9 / 5) + 32
                unit = "°F"
            else:
                temp = temp_c
                unit = "°C"

            #Get matching icon image
            icon_path = icon_map.get(summary, "icons/icons8-question-mark-50.png")

            #Create an individual forecast block (day card)
            frame = ttk.Frame(self.forecast_frame, width=140)
            frame.pack(side="left", padx=12, pady=5, anchor="n", fill="y")

            #Load and display weather icon
            try:
                img = Image.open(icon_path).resize((48, 48))
                photo = ImageTk.PhotoImage(img)
                icon_label = tk.Label(frame, image=photo)
                icon_label.image = photo  # type: ignore
                icon_label.pack()
            except Exception as e:
                print(f"[Forecast Icon Error] {e}")

            #Show forecast date
            ttk.Label(frame, text=date, font=("Segoe UI", 10, "bold")).pack()

            #Display converted temperature
            ttk.Label(frame, text=f"{temp:.1f}{unit}", font=("Segoe UI", 10)).pack()

            #Show condition description (capitalized)
            ttk.Label(frame, text=detail.capitalize(), font=("Segoe UI", 10)).pack()

    def save_to_csv(self):
        #Export all weather readings in the database to a CSV file
        output_path = "./data/weather_readings.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Create folder if missing
        success = self.db.export_readings_to_csv(output_path)

        #Notify user on success/failure
        if success:
            messagebox.showinfo("✅ Exported", f"Saved to: {output_path}")
        else:
            messagebox.showwarning("⚠️ No Data", "No weather records available to export.")

    def run(self):
        #Launch the Tkinter event loop to start the app
        self.root.mainloop()