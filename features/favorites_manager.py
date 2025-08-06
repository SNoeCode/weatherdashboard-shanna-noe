# features/favorites_panel.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, timezone
from utils.date_time_utils import format_local_time

        
class FavoriteCityPanel:
    def __init__(self, parent_tab, tracker, db, logger, cfg):
        self.tracker = tracker
        self.db = db
        self.logger = logger
        self.cfg = cfg
  
        self.frame = ttk.Frame(parent_tab, padding=20)
        self.frame.pack(expand=True, fill='both')

        title = ttk.Label(self.frame, text="🌍 Favorite Cities Dashboard", font=("Segoe UI", 18, "bold"))
        title.pack(pady=10)

        self.display = tk.Text(self.frame, height=20, width=80, wrap=tk.WORD, bg="#e6f7ff", fg="#000066")
        self.display.pack(expand=True)

        ttk.Button(self.frame, text="🔄 Refresh", command=self.refresh).pack(pady=10)

    def refresh(self):
        self.display.delete(1.0, tk.END)
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

                self.display.insert(tk.END, f"📍 {city}, {country}\n", "title")
                
                if latest:
                    temp_f = latest["temp"]
                    desc = latest["weather_detail"].capitalize()
                    try:
                        timestamp_utc = datetime.fromisoformat(latest["timestamp"])
                        if timestamp_utc.tzinfo is None:
                            timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

                        now_utc = datetime.now(timezone.utc)
                        if now_utc - timestamp_utc > timedelta(hours=2):
                            self.display.insert(tk.END, "  ⚠️ Reading may be outdated\n")

                        formatted_time = format_local_time(timestamp_utc.isoformat(), tz_name=self.cfg.default_timezone)

                        self.display.insert(tk.END, f"  {temp_f:.1f}°F — {desc}\n")
                        self.display.insert(tk.END, f"  Last Reading: {formatted_time}\n")
                        self.display.insert(tk.END,
                            f"  Humidity: {latest['humidity']}%   Wind: {latest['wind_speed']} m/s   Pressure: {latest['pressure']} hPa\n")

                    except Exception as e:
                        self.logger.warning(f"⏳ Failed to parse timestamp: {e}")

                    last_status = conn.execute("""
                        SELECT status FROM request_log
                        WHERE location_id = ? ORDER BY timestamp DESC LIMIT 1
                    """, (loc_id,)).fetchone()

                    if last_status:
                        self.display.insert(tk.END,
                            f"  Last API Status: {last_status['status']}\n")
                else:
                    self.display.insert(tk.END, "  ❌ No weather data found\n")

                self.display.insert(tk.END,
                    f"  API Success Rate: {rate}   Errors: {errors}\n\n")

        self.display.tag_config("title", foreground="#0059b3", font=("Segoe UI", 12, "bold"))

    def add_city_to_favorites(self, city: str, country: str = "US"):
        if not city:
            messagebox.showwarning("❗ Missing City", "Enter a city before adding to favorites.")
            return

        if any(
            loc["city"].lower() == city.lower() and loc["country"].upper() == country.upper()
            for loc in self.tracker.get_active_locations()
        ):
            messagebox.showinfo("📌 Already Added", f"{city}, {country} is already a favorite.")
            return

        if self.tracker.add_location(city, country):
            messagebox.showinfo("⭐ Saved", f"{city}, {country} added to favorites.")
            self.refresh()
        else:
            messagebox.showwarning("⚠️ Error", "Could not add city to favorites.")
   