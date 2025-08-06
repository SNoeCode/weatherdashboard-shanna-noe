from collections import Counter, defaultdict 
from typing import Dict, Optional, Callable
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from weather_db import WeatherDB
from weather_data_fetcher import WeatherDataFetcher
from services.weather_stats import get_weather_stats

class SimpleStatsPanel:
    def __init__(self, parent_tab, fetcher, db, logger, tracker, cfg):
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger
        self.cfg = cfg
       
        self.main_frame = tk.Frame(parent_tab, bg='#f8fafc')
        self.main_frame.pack(fill='both', expand=True)

        self.create_stats_interface()
        self.refresh_stats()

    def create_stats_interface(self):
        # Title section
        title_frame = tk.Frame(self.main_frame, bg='#3b82f6', height=60)
        title_frame.pack(fill='x', pady=(0, 20))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="📊 Weather Statistics Dashboard", 
                              font=("Segoe UI", 18, "bold"), bg='#3b82f6', fg='#ffffff')
        title_label.pack(expand=True)

        # Controls section
        controls_frame = tk.Frame(self.main_frame, bg='#e0f2fe', relief='solid', bd=1)
        controls_frame.pack(fill='x', pady=(0, 20), padx=10)

        # Location settings 
        input_frame = tk.Frame(controls_frame, bg='#e0f2fe')
        input_frame.pack(pady=15, padx=15)

        # City input 
        city_frame = tk.Frame(input_frame, bg='#e0f2fe')
        city_frame.grid(row=0, column=0, padx=10, pady=5)
        tk.Label(city_frame, text="🏙️ City:", font=("Segoe UI", 10, "bold"), 
                bg='#e0f2fe', fg='#0f172a').pack()
        self.city_entry = tk.Entry(city_frame, width=15, font=("Segoe UI", 10),
                                  bg='#ffffff', fg='#1e293b', relief='flat', bd=2)
        self.city_entry.pack(pady=(5, 0))
        self.city_entry.insert(0, "Knoxville")

        # State input
        state_frame = tk.Frame(input_frame, bg='#e0f2fe')
        state_frame.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(state_frame, text="🗺️ State:", font=("Segoe UI", 10, "bold"), 
                bg='#e0f2fe', fg='#0f172a').pack()
        self.state_entry = tk.Entry(state_frame, width=8, font=("Segoe UI", 10),
                                   bg='#ffffff', fg='#1e293b', relief='flat', bd=2)
        self.state_entry.pack(pady=(5, 0))
        self.state_entry.insert(0, "TN")

        # Country input
        country_frame = tk.Frame(input_frame, bg='#e0f2fe')
        country_frame.grid(row=0, column=2, padx=10, pady=5)
        tk.Label(country_frame, text="🌍 Country:", font=("Segoe UI", 10, "bold"), 
                bg='#e0f2fe', fg='#0f172a').pack()
        self.country_entry = tk.Entry(country_frame, width=8, font=("Segoe UI", 10),
                                     bg='#ffffff', fg='#1e293b', relief='flat', bd=2)
        self.country_entry.pack(pady=(5, 0))
        self.country_entry.insert(0, "US")

        # Hours input
        hours_frame = tk.Frame(input_frame, bg='#e0f2fe')
        hours_frame.grid(row=0, column=3, padx=10, pady=5)
        tk.Label(hours_frame, text="⏰ Hours:", font=("Segoe UI", 10, "bold"), 
                bg='#e0f2fe', fg='#0f172a').pack()
        self.hours_entry = tk.Entry(hours_frame, width=8, font=("Segoe UI", 10),
                                   bg='#ffffff', fg='#1e293b', relief='flat', bd=2)
        self.hours_entry.pack(pady=(5, 0))
        self.hours_entry.insert(0, "48")

        # Buttons
        buttons_frame = tk.Frame(controls_frame, bg='#e0f2fe')
        buttons_frame.pack(pady=(0, 15))

        refresh_btn = tk.Button(buttons_frame, text="🔄 Refresh Stats", 
                               command=self.refresh_stats,
                               font=("Segoe UI", 10, "bold"),
                               bg='#10b981', fg='#ffffff', relief='flat', bd=0,
                               padx=20, pady=8, cursor='hand2')
        refresh_btn.pack(side='left', padx=(0, 10))

        export_btn = tk.Button(buttons_frame, text="💾 Export Data", 
                              command=self.export_data,
                              font=("Segoe UI", 10, "bold"),
                              bg='#f59e0b', fg='#ffffff', relief='flat', bd=0,
                              padx=20, pady=8, cursor='hand2')
        export_btn.pack(side='left')

        # Stats display area
        stats_container = tk.Frame(self.main_frame, bg='#ffffff', relief='solid', bd=1)
        stats_container.pack(fill='both', expand=True, padx=10)

        # Stats header
        stats_header = tk.Frame(stats_container, bg='#6366f1', height=40)
        stats_header.pack(fill='x')
        stats_header.pack_propagate(False)
        
        header_label = tk.Label(stats_header, text="📊 Statistics Report", 
                               font=("Segoe UI", 12, "bold"), 
                               bg='#6366f1', fg='#ffffff')
        header_label.pack(expand=True)

        # Stats text area 
        text_frame = tk.Frame(stats_container, bg='#ffffff')
        text_frame.pack(fill='both', expand=True, padx=15, pady=15)

        self.stats_text = tk.Text(text_frame, height=20, width=80, 
                                 font=("Consolas", 11), wrap='word',
                                 bg='#f8fafc', fg='#1e293b', relief='flat', bd=1)
        self.stats_text.pack(side='left', fill='both', expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame, orient="vertical", 
                               command=self.stats_text.yview,
                               bg='#e2e8f0', troughcolor='#f1f5f9')
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        
    def refresh_stats(self):
        try:
            city = self.city_entry.get().strip() or "Knoxville"
            state = self.state_entry.get().strip() or "TN"
            country = self.country_entry.get().strip() or "US"
            hours = int(self.hours_entry.get().strip() or "48")
            stats = get_weather_stats(self.db, city, state, country)
            self.display_stats(city, country, hours, stats)

        except ValueError:
            messagebox.showerror("Error", "Invalid hours value. Please enter a number.")
        except Exception as e:
            error_msg = f"Error loading statistics: {str(e)}"
            self.logger.error(error_msg)
            self.display_error(error_msg)

    def display_stats(self, city: str, country: str, hours: int, stats: Dict):
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)

        stats_text = f"""\
🌤️ WEATHER STATISTICS FOR {city.upper()}, {country.upper()}
{'═' * 65}

⏰ Analysis Period: Last {hours} hours
📅 Last Updated: {stats.get('last_updated', 'N/A')}

🌡️ TEMPERATURE ANALYSIS:
   • Average Temperature: {stats.get('avg_temp', 'N/A')}°F
   • Maximum Temperature: {stats.get('max_temp', 'N/A')}°F  
   • Minimum Temperature: {stats.get('min_temp', 'N/A')}°F
   • Temperature Range: {stats.get('temp_range', 'N/A')}°F

💧 HUMIDITY METRICS:
   • Average Humidity: {stats.get('humidity_avg', 'N/A')}%
   • Maximum Humidity: {stats.get('humidity_max', 'N/A')}%
   • Minimum Humidity: {stats.get('humidity_min', 'N/A')}%

🌬️ WIND CONDITIONS:
   • Average Wind Speed: {stats.get('wind_avg', 'N/A')} km/h
   • Maximum Wind Speed: {stats.get('wind_max', 'N/A')} km/h
   • Minimum Wind Speed: {stats.get('wind_min', 'N/A')} km/h

🌤️ WEATHER PATTERNS:
   • Most Common Condition: {stats.get('common_conditions', 'N/A')}
   • Total Conditions Recorded: {stats.get('condition_count', 'N/A')}

📊 DATA SUMMARY:
   • Total Readings: {stats.get('total_readings', 'N/A')}
   • Data Quality: {stats.get('data_quality', 'Excellent')}
   • Coverage: {stats.get('coverage_percentage', 'N/A')}%

{'═' * 65}
🎯 Generated by Weather Dashboard Pro - Enhanced Edition
        """
        self.stats_text.insert(tk.END, stats_text)
        self.stats_text.config(state='disabled')

    def display_error(self, error_msg: str):
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, f"❌ ERROR: {error_msg}\n\n💡 Try checking your connection or adjusting the location settings.")
        self.stats_text.config(state='disabled')

    def export_data(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save weather data as..."
            )

            if filename:
                success = self.db.export_readings_to_csv(filename)
                if success:
                    messagebox.showinfo("✅ Export Successful", f"Weather data exported to:\n{filename}")
                else:
                    messagebox.showwarning("⚠️ Export Failed", "No weather records available to export.")
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            messagebox.showerror("❌ Export Error", f"Failed to export data:\n{str(e)}")

    def render_to_frame(self, frame, city: str, state: str = "TN", country: str = "US", units: str = "metric"):
        try:
            for widget in frame.winfo_children():
                widget.destroy()

            stats = get_weather_stats(self.db, city, state, country)
            unit_symbol = "°F" if units == "imperial" else "°C"
           
            mini_frame = tk.Frame(frame, bg='#f0f9ff', relief='solid', bd=1)
            mini_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            header = tk.Frame(mini_frame, bg='#0ea5e9', height=35)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            tk.Label(header, text=f"📊 {city}, {country}", 
                    font=("Segoe UI", 12, "bold"), bg='#0ea5e9', fg='#ffffff').pack(expand=True)

            content = tk.Frame(mini_frame, bg='#f0f9ff')
            content.pack(fill='both', expand=True, padx=15, pady=15)

            stats_info = [
                ("🌡️ Min Temp:", f"{stats['min_temp']}{unit_symbol}", "#3b82f6"),
                ("🔥 Max Temp:", f"{stats['max_temp']}{unit_symbol}", "#ef4444"),
                ("☁️ Common:", f"{stats['common_conditions']}", "#10b981")
            ]

            for i, (label, value, color) in enumerate(stats_info):
                row_frame = tk.Frame(content, bg='#f0f9ff')
                row_frame.pack(fill='x', pady=3)
                
                tk.Label(row_frame, text=label, font=("Segoe UI", 10, "bold"),
                        bg='#f0f9ff', fg='#1e293b').pack(side='left')
                tk.Label(row_frame, text=value, font=("Segoe UI", 10, "bold"),
                        bg='#f0f9ff', fg=color).pack(side='right')

        except Exception as e:
            if self.logger:
                self.logger.error(f"Stats render error: {e}")
            error_frame = tk.Frame(frame, bg='#fef2f2', relief='solid', bd=1)
            error_frame.pack(fill='both', expand=True, padx=10, pady=10)
            tk.Label(error_frame, text=f"❌ Error: {str(e)}", 
                    font=("Segoe UI", 12), bg='#fef2f2', fg='#dc2626').pack(pady=20)