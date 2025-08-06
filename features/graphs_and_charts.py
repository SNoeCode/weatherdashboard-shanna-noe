import matplotlib.cm as cm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter, HourLocator, DayLocator
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.container import BarContainer
import pandas as pd
import logging

class WeatherGraphs:
    def __init__(self, theme_manager=None):
        self.theme_manager = theme_manager
        self.logger = logging.getLogger(__name__)     
        self.colors = {
            "primary": "#2563eb",
            "secondary": "#1e40af", 
            "accent": "#3b82f6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "light": "#f8fafc",
            "dark": "#1f2937",
            "muted": "#6b7280"
        }
        
    def get_theme_colors(self):      
        if self.theme_manager:
            return self.theme_manager.get_theme_colors()
        else:
            return {
                "bg_primary": self.colors["primary"],
                "bg_card": self.colors["light"], 
                "text_primary": self.colors["dark"],
                "text_muted": self.colors["muted"],
                "accent": self.colors["accent"],
                "success": self.colors["success"],
                "warning": self.colors["warning"]
            }
    
    def process_temperature_data(self, readings, country="US"):      
        temps = []
        times = []
        
        self.logger.info(f"Processing {len(readings)} readings for temperature data")
        
        for i, reading in enumerate(readings):
            try:
                temp = None               
       
                if 'temp' in reading and reading['temp'] is not None:
                    temp = float(reading['temp'])
             
                elif 'main' in reading and isinstance(reading['main'], dict):
                    if 'temp' in reading['main']:
                        temp = float(reading['main']['temp'])
             
                elif 'temperature' in reading and reading['temperature'] is not None:
                    temp = float(reading['temperature'])
                
                if temp is None:
                    self.logger.debug(f"No temperature found in reading {i}: {reading}")
                    continue
                              
                if country.upper() == "US":                  
                    if temp < 50:
                        temp = (temp * 9/5) + 32
                
                # Extract timestamp with better parsing
                time_obj = None
                
                if 'timestamp' in reading:
                    time_str = reading['timestamp']
                elif 'dt_txt' in reading:
                    time_str = reading['dt_txt']
                elif 'dt' in reading:
                    # Unix timestamp
                    time_obj = datetime.utcfromtimestamp(reading['dt'])
                elif 'created_at' in reading:
                    time_str = reading['created_at']
                else:
                    self.logger.debug(f"No timestamp found in reading {i}")
                    continue
                
                # Parse timestamp if not already converted
                if time_obj is None and 'time_str' in locals():
                    if isinstance(time_str, str):
                        try:
                            # Try ISO format first
                            if 'T' in time_str:
                                time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                                if time_obj.tzinfo:
                                    time_obj = time_obj.replace(tzinfo=None)
                            # Try standard format
                            else:
                                time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            # Try pandas parsing as last resort
                            try:
                                time_obj = pd.to_datetime(time_str).to_pydatetime()
                            except:
                                self.logger.debug(f"Could not parse timestamp: {time_str}")
                                continue
                    else:
                        time_obj = time_str
                
                if time_obj is None:
                    continue
                
                temps.append(temp)
                times.append(time_obj)
                
            except Exception as e:
                self.logger.debug(f"Error processing reading {i}: {e}")
                continue
        
        self.logger.info(f"Successfully processed {len(temps)} temperature readings")
        
        # Sort by time
        if temps and times:
            combined = list(zip(times, temps))
            combined.sort(key=lambda x: x[0])
            times, temps = zip(*combined)
            times = list(times)
            temps = list(temps)
        
        return temps, times
    
    def create_enhanced_line_chart(self, parent_frame, readings, country="US"):
     
        self.logger.info(f"Creating line chart with {len(readings)} readings")
        
        temps, times = self.process_temperature_data(readings, country)
        
        if not temps or len(temps) < 1:
            self._show_no_data_message(parent_frame, f"Processed 0 temperature readings from {len(readings)} input readings")
            return None
        
        colors = self.get_theme_colors()
        
        # Create figure 
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        if len(temps) > 50:
            # Used pandas for better resampling
            try:
                df = pd.DataFrame({'time': times, 'temp': temps})
                df = df.set_index('time').resample('1H').mean().dropna()
                times = df.index.tolist()
                temps = df['temp'].tolist()
                self.logger.info(f"Resampled to {len(temps)} data points")
            except Exception as e:
                self.logger.warning(f"Resampling failed: {e}")
        
        # Line plot
        ax.plot(times, temps, color=self.colors["primary"], linewidth=3, 
                marker='o', markersize=5, markerfacecolor=self.colors["accent"],
                markeredgecolor='white', markeredgewidth=1.5, alpha=0.9)
               
        ax.fill_between(times, temps, alpha=0.1, color=self.colors["primary"])
        
        unit = "°F" if country.upper() == "US" else "°C"
        ax.set_title(f'Temperature Trend - {len(temps)} Data Points', 
                    fontsize=18, fontweight='bold', color=self.colors["dark"], pad=25)
        ax.set_ylabel(f'Temperature ({unit})', fontsize=14, color=self.colors["dark"], fontweight='bold')
               
        self._format_enhanced_time_axis(ax, times)
              
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color=self.colors["muted"])
        ax.set_axisbelow(True)
           
        if temps:
            current_temp = temps[-1]
            min_temp = min(temps)
            max_temp = max(temps)
            avg_temp = np.mean(temps)
            
            stats_text = f'Current: {current_temp:.1f}{unit}\nAverage: {avg_temp:.1f}{unit}\nRange: {min_temp:.1f}° - {max_temp:.1f}°'
                    
            bbox_props = dict(boxstyle='round,pad=0.8', facecolor='white', 
                            edgecolor=self.colors["primary"], linewidth=2, alpha=0.95)
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   verticalalignment='top', fontsize=11, color=self.colors["dark"],
                   bbox=bbox_props, fontweight='bold')
              
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)  
               
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()
        
        self.logger.info("Line chart created successfully")
        return canvas
    
    def create_enhanced_bar_chart(self, parent_frame, readings, country="US"):        
        temps, times = self.process_temperature_data(readings, country)
        
        if not temps:
            self._show_no_data_message(parent_frame, "No temperature data available for bar chart")
            return None
        
        # Group by day for daily averages
        daily_temps = {}
        for temp, time in zip(temps, times):
            day_key = time.strftime('%m/%d')
            if day_key not in daily_temps:
                daily_temps[day_key] = []
            daily_temps[day_key].append(temp)
        
        # Calculate daily statistics
        days = list(daily_temps.keys())
        avg_temps = [np.mean(daily_temps[day]) for day in days]
        max_temps = [max(daily_temps[day]) for day in days]
        min_temps = [min(daily_temps[day]) for day in days]
        
        # Limit to recent days
        if len(days) > 10:
            days = days[-10:]
            avg_temps = avg_temps[-10:]
            max_temps = max_temps[-10:]
            min_temps = min_temps[-10:]
        
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Bar chart 
        x = np.arange(len(days))
        width = 0.25
        
        # Create bars 
        bars1 = ax.bar(x - width, max_temps, width, label='Max', 
                      color=self.colors["danger"], alpha=0.8, edgecolor='white', linewidth=1)
        bars2 = ax.bar(x, avg_temps, width, label='Average', 
                      color=self.colors["primary"], alpha=0.8, edgecolor='white', linewidth=1)
        bars3 = ax.bar(x + width, min_temps, width, label='Min', 
                      color=self.colors["accent"], alpha=0.8, edgecolor='white', linewidth=1)
        
        # Value labels
        unit = "°F" if country.upper() == "US" else "°C"
        
        def add_value_labels(bars, values):
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{value:.0f}°', ha='center', va='bottom', 
                       fontweight='bold', fontsize=9, color=self.colors["dark"])
        
        add_value_labels(bars1, max_temps)
        add_value_labels(bars2, avg_temps)
        add_value_labels(bars3, min_temps)        
        
        ax.set_title(f'Daily Temperature Comparison', 
                    fontsize=18, fontweight='bold', color=self.colors["dark"], pad=25)
        ax.set_ylabel(f'Temperature ({unit})', fontsize=14, color=self.colors["dark"], fontweight='bold')
        ax.set_xlabel('Date', fontsize=14, color=self.colors["dark"], fontweight='bold')
        
        # X-axis
        ax.set_xticks(x)
        ax.set_xticklabels(days, rotation=45, ha='right', fontsize=11)
        
        # Legend
        legend = ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_edgecolor(self.colors["primary"])
        legend.get_frame().set_alpha(0.9)
        
        # Grid
        ax.grid(True, alpha=0.3, axis='y', linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()
        
        return canvas
    
    def _format_enhanced_time_axis(self, ax, times):     
        if len(times) < 2:
            return
            
        time_span = times[-1] - times[0]
        
        if time_span.days > 30:
            # Monthly view
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator())
        elif time_span.days > 7:
            # Weekly view
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_minor_locator(mdates.DayLocator())
        elif time_span.days > 2:
            # Daily view
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
        elif time_span.days > 0:
            # Hourly view
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
        else:
            # Minute view
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=15))
        
        ax.tick_params(axis='x', rotation=45, labelsize=10, colors=self.colors["dark"])
        ax.tick_params(axis='y', labelsize=11, colors=self.colors["dark"])
        
        # Label alignment
        plt.setp(ax.xaxis.get_majorticklabels(), ha='right', fontweight='bold')
    
    def _show_no_data_message(self, parent_frame, detail_msg=""):      
        container = tk.Frame(parent_frame, bg='white')
        container.pack(fill='both', expand=True)
          
        icon_label = tk.Label(container, text="📊", font=("Segoe UI", 48), bg='white')
        icon_label.pack(pady=(50, 10))
        
        title_label = tk.Label(container, text="No Temperature Data Available", 
                              font=("Segoe UI", 16, "bold"), bg='white', fg=self.colors["dark"])
        title_label.pack(pady=(0, 5))
        
        if detail_msg:
            detail_label = tk.Label(container, text=detail_msg, 
                                   font=("Segoe UI", 10), bg='white', fg=self.colors["muted"])
            detail_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(container, text="Try searching for weather data first to view charts", 
                                 font=("Segoe UI", 12), bg='white', fg=self.colors["muted"])
        subtitle_label.pack(pady=(0, 20))
        
        # Debug info
        debug_label = tk.Label(container, text="💡 Tip: Make sure you've fetched weather data in the Dashboard tab", 
                              font=("Segoe UI", 10, "italic"), bg='white', fg=self.colors["warning"])
        debug_label.pack(pady=(0, 50))
    
    def create_enhanced_graph_selector(self, parent_frame, readings, country="US"):
        self.logger.info(f"Creating graph selector with {len(readings)} readings")
        
        control_frame = tk.Frame(parent_frame, bg='white', relief='solid', bd=1)
        control_frame.pack(fill='x', pady=(0, 15))
        
        # Header section
        header_frame = tk.Frame(control_frame, bg=self.colors["primary"], height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame, text="📊 Enhanced Weather Charts",
                              font=("Segoe UI", 18, "bold"),
                              bg=self.colors["primary"], fg="white")
        title_label.pack(side='left', padx=20, pady=15)
        
        # Data info with debugging
        temps, times = self.process_temperature_data(readings, country)
        info_text = f"Showing {len(temps)} temperature readings from {len(readings)} total readings"
        if not temps:
            info_text = f"No valid temperature data found in {len(readings)} readings"
            
        info_label = tk.Label(header_frame, text=info_text,
                             font=("Segoe UI", 11),
                             bg=self.colors["primary"], fg="#cbd5e1")
        info_label.pack(side='right', padx=20, pady=15)
        
        # Button section
        button_frame = tk.Frame(control_frame, bg='white', height=80)
        button_frame.pack(fill='x', padx=20, pady=15)
        button_frame.pack_propagate(False)
        
        # Graph type buttons
        graph_types = [
            ("📈 Enhanced Line", "line", self.colors["primary"]),
            ("📊 Multi-Bar", "bar", self.colors["success"]),
            ("🏔️ Area + Trends", "area", self.colors["warning"]),
            ("⚪ Smart Scatter", "scatter", self.colors["danger"])
        ]
        
        for i, (text, chart_type, color) in enumerate(graph_types):
            btn = tk.Button(button_frame, text=text,
                           font=("Segoe UI", 12, "bold"),
                           bg=color, fg="white",
                           padx=20, pady=10, cursor="hand2",
                           relief='flat', borderwidth=0,
                           command=lambda ct=chart_type: self._show_enhanced_graph(parent_frame, ct, readings, country))
            btn.grid(row=0, column=i, padx=5, sticky='ew')
            button_frame.grid_columnconfigure(i, weight=1)
        
        # Graph display area
        self.enhanced_graph_display_frame = tk.Frame(parent_frame, bg="white", relief="solid", bd=2)
        self.enhanced_graph_display_frame.pack(fill='both', expand=True)
        
        # Show line graph by default
        self._show_enhanced_graph(parent_frame, "line", readings, country)
    
    def _show_enhanced_graph(self, parent_frame, graph_type, readings, country):   
        if hasattr(self, 'enhanced_graph_display_frame'):
            for widget in self.enhanced_graph_display_frame.winfo_children():
                widget.destroy()
        
        try:          
            if graph_type == "line":
                self.create_enhanced_line_chart(self.enhanced_graph_display_frame, readings, country)
            elif graph_type == "bar":
                self.create_enhanced_bar_chart(self.enhanced_graph_display_frame, readings, country)
            elif graph_type == "area":
                self.create_enhanced_area_chart(self.enhanced_graph_display_frame, readings, country)
            elif graph_type == "scatter":
                self.create_enhanced_scatter_plot(self.enhanced_graph_display_frame, readings, country)
        except Exception as e:
            self.logger.error(f"Error creating {graph_type} chart: {e}")
            self._show_error_message(self.enhanced_graph_display_frame, f"Error creating {graph_type} chart: {str(e)}")
    
    def create_enhanced_area_chart(self, parent_frame, readings, country="US"):      
        temps, times = self.process_temperature_data(readings, country)
        
        if not temps:
            self._show_no_data_message(parent_frame, "No temperature data for area chart")
            return None
        
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Sample data if needed
        if len(temps) > 50:
            try:
                df = pd.DataFrame({'time': times, 'temp': temps})
                df = df.set_index('time').resample('2H').mean().dropna()
                times = df.index.tolist()
                temps = df['temp'].tolist()
            except Exception as e:
                self.logger.warning(f"Area chart resampling failed: {e}")
        
        # Enhanced area chart with gradient
        ax.plot(times, temps, color=self.colors["primary"], linewidth=3, alpha=0.9)
        ax.fill_between(times, temps, alpha=0.3, color=self.colors["primary"])
        
        # Add trend line
        if len(temps) > 2:
            time_nums = [mdates.date2num(t) for t in times]
            z = np.polyfit(time_nums, temps, 1)
            p = np.poly1d(z)
            trend_temps = [p(t) for t in time_nums]
            
            trend_color = self.colors["success"] if z[0] > 0 else self.colors["danger"]
            trend_direction = "↗ Rising" if z[0] > 0 else "↘ Falling"
            
            ax.plot(times, trend_temps, color=trend_color, linewidth=2, 
                   linestyle='--', alpha=0.8, label=f'Trend {trend_direction}')
        
        # Add average line
        avg_temp = np.mean(temps)
        ax.axhline(y=float(avg_temp), color=self.colors["warning"],
           linestyle=':', linewidth=2, alpha=0.8,
           label=f'Average: {avg_temp:.1f}°')
        
        unit = "°F" if country.upper() == "US" else "°C"
        ax.set_title(f'Temperature Area Chart with Trends', 
                    fontsize=18, fontweight='bold', color=self.colors["dark"], pad=25)
        ax.set_ylabel(f'Temperature ({unit})', fontsize=14, color=self.colors["dark"], fontweight='bold')
        
        # Enhanced axis formatting
        self._format_enhanced_time_axis(ax, times)
        
        # Enhanced grid and legend
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        legend = ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_alpha(0.9)
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()
        
        return canvas
    
    def create_enhanced_scatter_plot(self, parent_frame, readings, country="US"):       
        temps, times = self.process_temperature_data(readings, country)
        
        if not temps:
            self._show_no_data_message(parent_frame, "No temperature data for scatter plot")
            return None
        
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Create scatter plot 
        sizes = [30 + (i * 5) for i in range(len(temps))]  
        
        scatter = ax.scatter(times, temps, c=temps, cmap='RdYlBu_r', 
                           s=sizes, alpha=0.7, edgecolors='white', linewidth=1.5)
        
        # Add trend line
        if len(temps) > 2:
            time_nums = [mdates.date2num(t) for t in times]
            z = np.polyfit(time_nums, temps, 1)
            p = np.poly1d(z)
            trend_temps = [p(t) for t in time_nums]
            
            # Calculate R-squared
            y_mean = np.mean(temps)
            ss_tot = sum((y - y_mean) ** 2 for y in temps)
            ss_res = sum((temps[i] - trend_temps[i]) ** 2 for i in range(len(temps)))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            trend_direction = "↗" if z[0] > 0 else "↘"
            ax.plot(times, trend_temps, color=self.colors["danger"], linewidth=3, 
                   linestyle='--', alpha=0.8, 
                   label=f'Trend {trend_direction} (R²={r_squared:.3f})')
        
        unit = "°F" if country.upper() == "US" else "°C"
        ax.set_title(f'Temperature Distribution & Trends', 
                    fontsize=18, fontweight='bold', color=self.colors["dark"], pad=25)
        ax.set_ylabel(f'Temperature ({unit})', fontsize=14, color=self.colors["dark"], fontweight='bold')
        
        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, aspect=20)
        cbar.set_label(f'Temperature ({unit})', fontsize=12, color=self.colors["dark"], fontweight='bold')
        cbar.ax.tick_params(colors=self.colors["dark"])
        
        self._format_enhanced_time_axis(ax, times)
        
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        if len(temps) > 2:
            legend = ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_alpha(0.9)
        
        plt.tight_layout(pad=2.0)
        plt.subplots_adjust(bottom=0.15)
        
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()
        
        return canvas
    
    def _show_error_message(self, parent_frame, error_msg):        
        container = tk.Frame(parent_frame, bg='#fef2f2')
        container.pack(fill='both', expand=True)
        
        tk.Label(container, text="⚠️", font=("Segoe UI", 48), bg='#fef2f2').pack(pady=(30, 15))
        tk.Label(container, text="Graph Error", font=("Segoe UI", 18, "bold"), 
                bg='#fef2f2', fg="#dc2626").pack(pady=(0, 10))
        tk.Label(container, text=error_msg, font=("Segoe UI", 11), 
                bg='#fef2f2', fg="#7f1d1d", wraplength=400).pack(pady=(0, 30))


class GraphsAndChartsPanel:  
    def __init__(self, parent_frame, db, logger, theme_manager=None):
        self.parent_frame = parent_frame
        self.db = db
        self.logger = logger
        self.enhanced_graphs = WeatherGraphs(theme_manager)
        self.current_readings = []
        
        self.setup_enhanced_panel()
    
    def setup_enhanced_panel(self):
        # Enhanced header
        header_frame = tk.Frame(self.parent_frame, bg="#1e40af", height=100)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Title section
        title_label = tk.Label(header_frame, text="🚀 Enhanced Weather Analytics",
                              font=("Segoe UI", 24, "bold"),
                              bg="#1e40af", fg="white")
        title_label.pack(pady=(20, 5))
        
        subtitle_label = tk.Label(header_frame, text="Advanced charts with improved data processing and debugging",
                                 font=("Segoe UI", 12),
                                 bg="#1e40af", fg="#cbd5e1")
        subtitle_label.pack(pady=(0, 20))
        
        # Selection frame
        selection_frame = tk.Frame(self.parent_frame, bg="#f8fafc", relief='solid', bd=1)
        selection_frame.pack(fill='x', padx=20, pady=20)
        
        inner_frame = tk.Frame(selection_frame, bg="#f8fafc")
        inner_frame.pack(pady=20)
        
        tk.Label(inner_frame, text="📍 Location:", font=("Segoe UI", 12, "bold"),
                bg="#f8fafc", fg="#1f2937").grid(row=0, column=0, padx=(0, 10), sticky='w')
        
        self.city_var = tk.StringVar(value="Knoxville")
        city_entry = tk.Entry(inner_frame, textvariable=self.city_var, 
                             font=("Segoe UI", 11), width=18, relief='solid', bd=1)
        city_entry.grid(row=0, column=1, padx=(0, 15))
        
        tk.Label(inner_frame, text="🌍 Country:", font=("Segoe UI", 12, "bold"),
                bg="#f8fafc", fg="#1f2937").grid(row=0, column=2, padx=(0, 10))
        
        self.country_var = tk.StringVar(value="US")
        country_entry = tk.Entry(inner_frame, textvariable=self.country_var, 
                                font=("Segoe UI", 11), width=8, relief='solid', bd=1)
        country_entry.grid(row=0, column=3, padx=(0, 20))
                     
        load_btn = tk.Button(inner_frame, text="🚀 Load Enhanced Charts",
                            font=("Segoe UI", 12, "bold"),
                            bg="#2563eb", fg="white",
                            padx=25, pady=8, cursor="hand2", relief='flat',
                            command=self.load_enhanced_city_data)
        load_btn.grid(row=0, column=5)
        
        # Charts container
        self.enhanced_charts_container = tk.Frame(self.parent_frame, bg="#f8fafc")
        self.enhanced_charts_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Load default data
        self.load_enhanced_city_data()
    
    def debug_data(self):     
        city = self.city_var.get().strip() or "Knoxville"
        country = self.country_var.get().strip() or "US"
        
        self.logger.info(f"=== DEBUGGING DATA FOR {city}, {country} ===")
        
        try:
            # Check all readings in database
            all_readings = self.db.get_all_readings()
            self.logger.info(f"Total readings in database: {len(all_readings)}")
            
            # Check specific city readings
            city_readings = [r for r in all_readings 
                            if r.get('city', '').lower() == city.lower() 
                            and r.get('country', '').lower() == country.lower()]
            self.logger.info(f"Readings for {city}, {country}: {len(city_readings)}")
            
            if city_readings:
                sample = city_readings[0]
                self.logger.info(f"Sample reading structure: {sample}")
                self.logger.info(f"Sample keys: {list(sample.keys())}")
            
            # Check recent readings
            recent = self.db.fetch_recent(city, country, 168)  # 1 week
            self.logger.info(f"Recent readings (1 week): {len(recent)}")
            
            if recent:
                sample_recent = recent[0]
                self.logger.info(f"Recent reading structure: {sample_recent}")
                    
            try:
                current = self.db.fetch_current_weather(city, country)
                if current:
                    self.logger.info(f"Current weather available: {current}")
                else:
                    self.logger.info("No current weather data")
            except Exception as e:
                self.logger.error(f"Error fetching current weather: {e}")
                
        except Exception as e:
            self.logger.error(f"Debug error: {e}")
          
        import tkinter.messagebox as msgbox
        msgbox.showinfo("Debug Complete", 
                       f"Debug information logged for {city}, {country}.\n"
                       f"Check console/logs for details.\n"
                       f"Total readings: {len(all_readings) if 'all_readings' in locals() else 'Error'}\n"
                       f"City readings: {len(city_readings) if 'city_readings' in locals() else 'Error'}")
    
    def load_enhanced_city_data(self):     
        try:
            city = self.city_var.get().strip() or "Knoxville"
            country = self.country_var.get().strip() or "US"
            
            self.logger.info(f"Loading data for {city}, {country}")
                    
            readings = []            
       
            try:
                readings = self.db.fetch_recent(city, country, 168)  # 1 week
                self.logger.info(f"Method 1 (fetch_recent): {len(readings)} readings")
            except Exception as e:
                self.logger.warning(f"fetch_recent failed: {e}")
                       
            if not readings:
                try:
                    all_readings = self.db.get_all_readings()
                    readings = [r for r in all_readings 
                               if r.get('city', '').lower() == city.lower() 
                               and r.get('country', '').lower() == country.lower()]
                    self.logger.info(f"Method 2 (filtered all): {len(readings)} readings")
                except Exception as e:
                    self.logger.warning(f"get_all_readings failed: {e}")
                  
            if not readings:
                try:
                    self.logger.info("No existing data found, attempting to fetch current weather...")
                    current_weather = self.db.fetch_current_weather(city, country)
                    if current_weather:
                        readings = [current_weather]
                        self.logger.info(f"Method 3 (new fetch): 1 reading")
                except Exception as e:
                    self.logger.warning(f"fetch_current_weather failed: {e}")
            
            if readings:
                self.current_readings = readings
                # Clear existing charts
                for widget in self.enhanced_charts_container.winfo_children():
                    widget.destroy()
                
                # Create graph selector
                self.enhanced_graphs.create_enhanced_graph_selector(
                    self.enhanced_charts_container, readings, country)
                
                self.logger.info(f"Successfully loaded {len(readings)} readings for {city}, {country}")
            else:
                # No data message
                self._show_enhanced_no_data_message(city, country)
                
        except Exception as e:
            self.logger.error(f"Error loading enhanced city data: {e}")
            self._show_error_message(str(e))
    
    def _show_enhanced_no_data_message(self, city, country):    
        for widget in self.enhanced_charts_container.winfo_children():
            widget.destroy()
        
        container = tk.Frame(self.enhanced_charts_container, bg='white', relief='solid', bd=1)
        container.pack(fill='both', expand=True, padx=50, pady=50)
        
        # Large icon
        icon_label = tk.Label(container, text="📊", font=("Segoe UI", 64), bg='white')
        icon_label.pack(pady=(30, 20))
        
        # Title
        title_label = tk.Label(container, text=f"No Weather Data Available",
                              font=("Segoe UI", 20, "bold"), bg='white', fg="#1f2937")
        title_label.pack(pady=(0, 10))
        
        # Location info
        location_label = tk.Label(container, text=f"for {city}, {country}",
                                 font=("Segoe UI", 14), bg='white', fg="#6b7280")
        location_label.pack(pady=(0, 20))
        
        # Suggestions
        suggestions_frame = tk.Frame(container, bg='white')
        suggestions_frame.pack(pady=20)
        
        tk.Label(suggestions_frame, text="💡 Troubleshooting Steps:",
                font=("Segoe UI", 14, "bold"), bg='white', fg="#1f2937").pack(anchor='w')
        
        suggestions = [
            "1. Click '🔍 Debug Data' to check what data is available",
            "2. Search for weather data in the Dashboard tab first",
            "3. Try a different city name or country code",
            "4. Check your internet connection",
            "5. Wait a few minutes and try again"
        ]
        
        for suggestion in suggestions:
            tk.Label(suggestions_frame, text=suggestion,
                    font=("Segoe UI", 11), bg='white', fg="#6b7280").pack(anchor='w', pady=2)
    
    def _show_error_message(self, error_msg):      
        for widget in self.enhanced_charts_container.winfo_children():
            widget.destroy()
        
        error_container = tk.Frame(self.enhanced_charts_container, bg='#fef2f2', relief='solid', bd=1)
        error_container.pack(fill='both', expand=True, padx=50, pady=50)
        
        # Error icon
        tk.Label(error_container, text="⚠️", font=("Segoe UI", 48), bg='#fef2f2').pack(pady=(30, 15))
        
        # Error title
        tk.Label(error_container, text="Error Loading Data",
                font=("Segoe UI", 18, "bold"), bg='#fef2f2', fg="#dc2626").pack(pady=(0, 10))
        
        # Error message
        tk.Label(error_container, text=f"Details: {error_msg}",
                font=("Segoe UI", 11), bg='#fef2f2', fg="#7f1d1d", 
                wraplength=400).pack(pady=(0, 30))


# Integration functions
def integrate_charts(parent_frame, db, logger, theme_manager=None):    
    return GraphsAndChartsPanel(parent_frame, db, logger, theme_manager)

def fix_dashboard_temperature_graph(graph_container, readings, country="US"):
    logger = logging.getLogger(__name__)
    
    try:
        # Clear existing graph
        for widget in graph_container.winfo_children():
            widget.destroy()
        
        logger.info(f"Creating dashboard graph with {len(readings)} readings")
        
        if not readings:
            placeholder = tk.Label(graph_container,
                                text="📈 Temperature trend will appear\nafter weather data is collected",
                                font=("Segoe UI", 12), bg="white", fg="#6b7280")
            placeholder.pack(expand=True)
            return
        
        # Process temperature data
        weather_graphs = WeatherGraphs()
        temps, times = weather_graphs.process_temperature_data(readings, country)
        
        if not temps or len(temps) < 1:
            logger.warning(f"No valid temperature data found in {len(readings)} readings")
            placeholder = tk.Label(graph_container,
                                text="📈 No valid temperature data found\nTry fetching weather data first",
                                font=("Segoe UI", 12), bg="white", fg="#e74c3c")
            placeholder.pack(expand=True)
            return
        
        logger.info(f"Processed {len(temps)} temperature readings for dashboard graph")
        
        # Create compact graph
        fig, ax = plt.subplots(figsize=(6, 3.5))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Sample data if too many points
        if len(temps) > 24:
            step = len(temps) // 24
            temps = temps[::step]
            times = times[::step]
        
        # Line plot
        ax.plot(times, temps, color='#2563eb', linewidth=2.5, marker='o', 
                markersize=4, markerfacecolor='#3b82f6', markeredgewidth=0)
        
        # Add fill
        ax.fill_between(times, temps, alpha=0.2, color='#2563eb')
        
        # Title and labels
        unit = "°F" if country.upper() == "US" else "°C"
        ax.set_title(f'Temperature Trend - {len(temps)} Points', 
                    fontsize=12, fontweight='bold', color='#1f2937', pad=15)
        
        # Format time axis
        if len(times) > 1:
            time_span = times[-1] - times[0]
            if time_span.days > 1:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            else:
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(4, len(times)//6)))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Styling
        ax.tick_params(labelsize=9, colors='#374151')
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Rotate labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
        
        # Current temperature display
        if temps:
            current_temp = temps[-1]
            ax.text(0.02, 0.98, f'{current_temp:.0f}{unit}', 
                   transform=ax.transAxes, fontsize=14, fontweight='bold',
                   verticalalignment='top', color='#1f2937',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                           edgecolor='#2563eb', alpha=0.9))
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.2)
            
        canvas = FigureCanvasTkAgg(fig, graph_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        logger.info("Dashboard temperature graph created successfully")
        
    except Exception as e:
        logger.error(f"Error creating dashboard graph: {e}")
        error_label = tk.Label(graph_container,
                             text="📈 Graph temporarily unavailable\nCheck logs for details",
                             font=("Segoe UI", 12), bg="white", fg="#e74c3c")
        error_label.pack(expand=True)
