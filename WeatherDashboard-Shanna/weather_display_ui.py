from collections import defaultdict
from datetime import datetime, timedelta, timezone

import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
from dotenv import load_dotenv
from config import Config
from config import setup_logger
from typing import cast, Optional
from features.simple_statisitics import get_weather_stats
from utils.date_time import format_local_time
from features.weather_icons import display_weather_with_icon, get_icon_path
from features.weather_history_tracker import render_five_day_forecast as render_forecast
from features.city_comparisons import setup_comparison_tab
load_dotenv()
cfg = Config.load_from_env()


class WeatherAppGUI:
    def __init__(self, fetcher, db, tracker, logger):
        #Store core components (weather fetcher, database, automated tracker, logger)
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger
        #Create main window with defined size and background
        self.root = tk.Tk()
        self.root.title("🌤️ Weather Dashboard")  
        self.root.geometry("1000x700")         
        self.root.configure(bg="#f0f8ff")     
        self.city1_entry: Optional[ttk.Entry] = None
        self.city2_entry: Optional[ttk.Entry] = None
        self.compare_frame: Optional[ttk.LabelFrame] = None
       
        
     

        style = ttk.Style()
        style.theme_use("clam") 
        style.configure("TButton", font=("Segoe UI", 10, "bold"), foreground="#ffffff", background="#006699")  # Deeper blue
        style.map("TButton", foreground=[('active', '#ffffff')], background=[('active', '#004466')])
        style.configure("TLabel", background="#f7fbff", font=("Segoe UI", 11), foreground="#333")
        style.configure("TLabelframe.Label", font=("Segoe UI", 12, "bold"), foreground="#004080")
        style.configure("TLabelframe", background="#f7fbff", bordercolor="#3399ff")

        self.root.configure(bg="#f7fbff")  
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

       
        self.home_tab = ttk.Frame(self.notebook)
        self.favorites_tab = ttk.Frame(self.notebook)
        self.compare_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.home_tab, text="🏠 Home")
        self.notebook.add(self.favorites_tab, text="🌍 Favorites")
        self.notebook.add(self.compare_tab, text="🆚 Compare Cities")
        self.notebook.add(self.data_tab, text="📄 Database View")


        
        #Build contents of each tab
        self.setup_home_tab()
        self.setup_favorites_tab()
        setup_comparison_tab(self)
        self.setup_data_tab() 

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
        self.city_entry.insert(0, "Knoxville")  

        #Country input
        ttk.Label(frame, text="Country:").grid(row=1, column=2, sticky="e")
        self.country_entry = ttk.Entry(frame, width=10)
        self.country_entry.grid(row=1, column=3, padx=5)
        self.country_entry.insert(0, "US")  

        #Search button to trigger weather fetch
        self.search_button = ttk.Button(frame, text="Get Weather", command=self.get_weather_threaded)
        self.search_button.grid(row=1, column=4, padx=10)

        #Weather display box
        self.weather_frame = ttk.LabelFrame(frame, text="Current Weather", padding=10)
        self.weather_frame.grid(row=2, column=0, columnspan=5, pady=20, sticky="ew")
        self.weather_frame.columnconfigure(0, weight=1)
        self.view_mode = tk.StringVar(value="current")
        self.view_mode = tk.StringVar(value="current")
        ttk.Radiobutton(frame, text="🌤️ Now", variable=self.view_mode, value="current").grid(row=3, column=0, padx=5, pady=5)
        ttk.Radiobutton(frame, text="📆 7-Day", variable=self.view_mode, value="forecast").grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(frame, text="⭐ Save to Favorites", command=self.add_to_favorites).grid(row=5, column=0, columnspan=5, pady=10)
        ttk.Button(frame, text="💾 Save All to CSV", command=self.save_to_csv).grid(row=3, column=0, columnspan=5, pady=10)

    def setup_favorites_tab(self):
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
        self.favorites_display.delete(1.0, tk.END)
        locations = self.tracker.get_active_locations()

        with self.db.get_connection() as conn:
            for loc in locations:
                city, country, loc_id = loc["city"], loc["country"], loc["id"]

                latest = conn.execute("""
                    SELECT temp, weather_detail, humidity, wind_speed, pressure, timestamp
                    FROM readings WHERE city = ? AND country = ?
                    ORDER BY timestamp DESC LIMIT 1
                    """, (city, country)).fetchone()

                logs = conn.execute("""
                    SELECT status, COUNT(*) FROM request_log
                    WHERE location_id = ? AND timestamp > datetime('now', '-24 hours')
                    GROUP BY status
                """, (loc_id,)).fetchall()

                status_counts = {row["status"]: row["COUNT(*)"] for row in logs}
                success = status_counts.get("success", 0)
                errors = sum(c for s, c in status_counts.items() if s != "success")
                total = success + errors
                rate = f"{(success / total * 100):.1f}%" if total else "N/A"

                self.favorites_display.insert(tk.END, f"📍 {city}, {country}\n", "title")

                if latest:
                    temp_f = (latest["temp"] * 9/5) + 32
                    desc = latest["weather_detail"].capitalize()

                    try:
                        # Convert to aware UTC datetime
                        timestamp_utc = datetime.fromisoformat(latest["timestamp"])
                        if timestamp_utc.tzinfo is None:
                            timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

                        # Compare with current UTC time
                        now_utc = datetime.now(timezone.utc)
                        if now_utc - timestamp_utc > timedelta(hours=2):
                            self.favorites_display.insert(tk.END, "  ⚠️ Reading may be outdated\n")

                        # Format timestamp for display in user timezone
                        formatted_time = format_local_time(timestamp_utc.isoformat(), tz_name=cfg.default_timezone)

                        # Display weather data
                        self.favorites_display.insert(tk.END, f"  {temp_f:.1f}°F — {desc}\n")
                        self.favorites_display.insert(tk.END, f"  Last Reading: {formatted_time}\n")
                        self.favorites_display.insert(tk.END,
                            f"  Humidity: {latest['humidity']}%   Wind: {latest['wind_speed']} m/s   Pressure: {latest['pressure']} hPa\n")

                    except Exception as e:
                        self.logger.warning(f"⏳ Failed to parse timestamp: {e}")


                    last_status = conn.execute("""
                        SELECT status FROM request_log
                        WHERE location_id = ? ORDER BY timestamp DESC LIMIT 1
                    """, (loc_id,)).fetchone()

                    if last_status:
                        self.favorites_display.insert(tk.END,
                            f"  Last API Status: {last_status['status']}\n")
                else:
                    self.favorites_display.insert(tk.END, "  ❌ No weather data found\n")

                self.favorites_display.insert(tk.END,
                    f"  API Success Rate: {rate}   Errors: {errors}\n\n")

        self.favorites_display.tag_config("title", foreground="#0059b3", font=("Segoe UI", 12, "bold"))



    def get_weather_threaded(self):
        threading.Thread(target=self.get_weather, daemon=True).start()

    def get_weather(self):
        city = self.city_entry.get().strip()
        country = self.country_entry.get().strip() or "US"

        self.city_entry.delete(0, tk.END)
        self.country_entry.delete(0, tk.END)

        if not city:
            messagebox.showwarning("Missing Input", "Please enter a city name.")
            return

        for widget in self.weather_frame.winfo_children():
            widget.destroy()

        if self.view_mode.get() == "current":
            result = self.fetcher.fetch_current_weather(city, country)
            if result:
                self.db.insert_reading(result)
                self.tracker.database.log_request("manual_search", None, "success")
                display_weather_with_icon(self.weather_frame, result, self.fetcher, render_forecast)
            else:
                messagebox.showerror("Weather Error", "Could not fetch current conditions.")
        else:
            forecast = self.fetcher.fetch_five_day_forecast(city, country)
            if forecast and "list" in forecast:
                render_forecast(self.weather_frame, forecast, country)
            else:
                messagebox.showerror("⚠️ Forecast Error", "Could not retrieve 5-day forecast for this city.")
                
                
    def add_to_favorites(self):
        city = self.city_entry.get().strip()
        country = self.country_entry.get().strip() or "US"  # fallback to US

        if city:
            # Check if already added
            if any(
                loc["city"].lower() == city.lower() and loc["country"].upper() == country.upper()
                for loc in self.tracker.get_active_locations()
            ):
                messagebox.showinfo("📌 Already Added", f"{city}, {country} is already a favorite.")
                return

            added = self.tracker.add_location(city, country)
            if added:
                messagebox.showinfo("⭐ Saved", f"{city}, {country} added to favorites.")
                self.refresh_favorites()
            else:
                messagebox.showwarning("⚠️ Error", "Could not add city to favorites.")
        else:
            messagebox.showwarning("❗ Missing City", "Enter a city before adding to favorites.")
    def compare_cities(self):
        if not self.city1_entry or not self.city2_entry or not self.compare_frame:
            self.logger.error("Comparison UI not initialized properly.")
            return

        city_a = self.city1_entry.get().strip()
        city_b = self.city2_entry.get().strip()
        country = "US"

        for widget in self.compare_frame.winfo_children():
            widget.destroy()

        data_a = self.fetcher.fetch_current_weather(city_a, country)
        data_b = self.fetcher.fetch_current_weather(city_b, country)

        if not data_a or not data_b:
            messagebox.showerror("❌ Compare Error", "Could not fetch weather for one or both cities.")
            return

        stats_a = get_weather_stats(self.db, data_a["city"], data_a["country"])
        stats_b = get_weather_stats(self.db, data_b["city"], data_b["country"])

        for idx, (data, stats) in enumerate(zip([data_a, data_b], [stats_a, stats_b])):
            card = ttk.LabelFrame(self.compare_frame, text=f"{data['city']}", padding=10)
            card.grid(row=0, column=idx, padx=10)

            icon_path = get_icon_path(data["weather_summary"])
            try:
                img = Image.open(icon_path).resize((48, 48))
                photo = ImageTk.PhotoImage(img)
                icon = tk.Label(card, image=photo)
                icon.image = photo  # type: ignore
                icon.pack()
            except Exception as e:
                print(f"[Icon Error] {e}")

            temp_f = (data['temp'] * 9 / 5) + 32
            desc = data["weather_detail"].capitalize()
            ttk.Label(card, text=f"{desc}, {temp_f:.1f}°F").pack()


            ttk.Label(card, text=f"Humidity: {data['humidity']}%").pack()
            ttk.Label(card, text=f"Wind: {data['wind_speed']} m/s").pack()
            ttk.Label(card, text=f"Pressure: {data['pressure']} hPa").pack()
            if stats:
                ttk.Label(card, text=f"Common: {stats['common_conditions']}").pack()
                ttk.Label(card, text=f"Min/Max: {stats['min_temp']:.1f}°C / {stats['max_temp']:.1f}°C").pack()


    def refresh_data_view(self):
        self.locations_box.delete("1.0", tk.END)
        self.readings_box.delete("1.0", tk.END)

        locations = self.db.get_all_locations()
        readings = self.db.get_all_readings()

        for loc in locations:
            self.locations_box.insert(tk.END, f"{loc}\n")

        for r in readings:
            line = f"{r['city']}, {r['country']} | {r['temp']}°C, {r['weather_summary']} | {r['timestamp']}"
            self.readings_box.insert(tk.END, f"{line}\n")
            
        
    def setup_data_tab(self):
        frame = ttk.Frame(self.data_tab, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="📍 Locations").grid(row=0, column=0, sticky="w")
        self.locations_box = tk.Text(frame, height=10, width=90)
        self.locations_box.grid(row=1, column=0, pady=5)

        ttk.Label(frame, text="🌡️ Readings").grid(row=2, column=0, sticky="w")
        self.readings_box = tk.Text(frame, height=10, width=90)
        self.readings_box.grid(row=3, column=0, pady=5)

        ttk.Button(frame, text="🔄 Refresh", command=self.refresh_data_view).grid(row=4, column=0, pady=10)

    def save_to_csv(self):
        output_path = "./data/weather_readings.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)         
        success = self.db.export_readings_to_csv(output_path)
        if success:
            messagebox.showinfo("✅ Exported", f"Saved to: {output_path}")
        else:
            messagebox.showwarning("⚠️ No Data", "No weather records available to export.")

    def run(self):
        self.root.mainloop()