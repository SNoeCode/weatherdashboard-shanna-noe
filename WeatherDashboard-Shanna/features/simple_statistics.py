from collections import Counter, defaultdict
from typing import Dict, Optional
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
        
        # Create main container
        self.main_frame = ttk.Frame(parent_tab, padding=20)
        self.main_frame.pack(fill='both', expand=True)
        
        # Create stats 
        self.create_stats_interface()
        
        # Load data
        self.refresh_stats()

    def create_stats_interface(self):
        title_label = ttk.Label(self.main_frame, text="📊 Weather Statistics Dashboard", 
                               font=("Segoe UI", 20, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Controls 
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(fill='x', pady=(0, 20))
        
        input_frame = ttk.LabelFrame(controls_frame, text="🌍 Location Settings", padding=10)
        input_frame.pack(fill='x', pady=(0, 10))
        
        input_grid = ttk.Frame(input_frame)
        input_grid.pack(fill='x')
        
        ttk.Label(input_grid, text="City:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.city_entry = ttk.Entry(input_grid, width=20)
        self.city_entry.grid(row=0, column=1, padx=(0, 20))
        self.city_entry.insert(0, "Knoxville")
        
        ttk.Label(input_grid, text="Country:").grid(row=0, column=2, sticky='w', padx=(0, 5))
        self.country_entry = ttk.Entry(input_grid, width=10)
        self.country_entry.grid(row=0, column=3, padx=(0, 20))
        self.country_entry.insert(0, "US")
        
        ttk.Label(input_grid, text="Hours:").grid(row=0, column=4, sticky='w', padx=(0, 5))
        self.hours_entry = ttk.Entry(input_grid, width=10)
        self.hours_entry.grid(row=0, column=5, padx=(0, 20))
        self.hours_entry.insert(0, "48")
        
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill='x')
        
        refresh_btn = ttk.Button(buttons_frame, text="🔄 Refresh Stats", 
                                command=self.refresh_stats)
        refresh_btn.pack(side='left', padx=(0, 10))
        
        export_btn = ttk.Button(buttons_frame, text="💾 Export Data", 
                               command=self.export_data)
        export_btn.pack(side='left')
        
        # Stats display 
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="📊 Statistics", padding=20)
        self.stats_frame.pack(fill='both', expand=True)
        
        self.stats_text = tk.Text(self.stats_frame, height=20, width=80, 
                                 font=("Consolas", 11), wrap='word')
        self.stats_text.pack(fill='both', expand=True)
        
        # scrollbar
        scrollbar = ttk.Scrollbar(self.stats_frame, orient="vertical", command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def refresh_stats(self):
        try:
            city = self.city_entry.get().strip() or "Knoxville"
            country = self.country_entry.get().strip() or "US"
            hours = int(self.hours_entry.get().strip() or "48")
            
           
            stats = get_weather_stats(self.db, city, country)
            self.display_stats(city, country, hours, stats)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid hours value. Please enter a number.")
        except Exception as e:
            error_msg = f"Error loading statistics: {str(e)}"
            self.logger.error(error_msg)
            self.display_error(error_msg)

    def display_stats(self, city: str, country: str, hours: int, stats: Dict):
        # Clear current content
        self.stats_text.delete(1.0, tk.END)
        
        # Format statistics
        stats_text = f"""
        📊 WEATHER STATISTICS FOR {city.upper()}, {country.upper()}
        {'=' * 60}

        🕐 Time Period: Last {hours} hours
        📅 Data Updated: {stats.get('last_updated', 'N/A')}

        🌡️ TEMPERATURE STATISTICS:
        • Average Temperature: {stats.get('avg_temp', 'N/A')}°F
        • Maximum Temperature: {stats.get('max_temp', 'N/A')}°F
        • Minimum Temperature: {stats.get('min_temp', 'N/A')}°F
        • Temperature Range: {stats.get('temp_range', 'N/A')}°F

        💧 HUMIDITY STATISTICS:
        • Average Humidity: {stats.get('humidity_avg', 'N/A')}%
        • Maximum Humidity: {stats.get('humidity_max', 'N/A')}%
        • Minimum Humidity: {stats.get('humidity_min', 'N/A')}%

        🌬️ WIND STATISTICS:
        • Average Wind Speed: {stats.get('wind_avg', 'N/A')} km/h
        • Maximum Wind Speed: {stats.get('wind_max', 'N/A')} km/h
        • Minimum Wind Speed: {stats.get('wind_min', 'N/A')} km/h

        🌤️ WEATHER CONDITIONS:
        • Most Common Condition: {stats.get('common_conditions', 'N/A')}
        • Total Conditions Recorded: {stats.get('condition_count', 'N/A')}

        📊 DATA SUMMARY:
        • Total Readings: {stats.get('total_readings', 'N/A')}
        • Data Quality: {stats.get('data_quality', 'Good')}
        • Coverage: {stats.get('coverage_percentage', 'N/A')}%

        {'=' * 60}
        📈 Generated by Weather Dashboard Pro
        """       
        # Insert txt
        self.stats_text.insert(tk.END, stats_text)
        
        # Makeread-only
        self.stats_text.config(state='disabled')

    def display_error(self, error_msg: str):
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, f"❌ ERROR: {error_msg}")
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
                    messagebox.showinfo("Export Successful", 
                                      f"Weather data exported to:\n{filename}")
                else:
                    messagebox.showwarning("Export Failed", 
                                         "No weather records available to export.")
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")

    def render_to_frame(self, frame, city: str, country: str, hours: int = 48, units: str = "metric"):
        try:
            for widget in frame.winfo_children():
                widget.destroy()
             
            stats = get_weather_stats(self.db, city, country)
             
            unit_symbol = "°F" if units == "imperial" else "°C"
            output = (
                f"📊 Statistics for {city}, {country}:\n\n"
                f"• Min Temp: {stats['min_temp']}{unit_symbol}\n"
                f"• Max Temp: {stats['max_temp']}{unit_symbol}\n"
                f"• Common Condition: {stats['common_conditions']}"
            )
             
            label = ttk.Label(frame, text=output, font=("Segoe UI", 12), justify="left")
            label.pack(padx=20, pady=20, anchor='w')
         
        except Exception as e:
            if self.logger:
                self.logger.error(f"Stats render error: {e}")
            ttk.Label(frame, text=f"❌ Error: {str(e)}", font=("Segoe UI", 12)).pack()