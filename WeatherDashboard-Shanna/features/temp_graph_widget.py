import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter, HourLocator
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
import numpy as np
from utils.date_time import format_local_time

class TemperatureGraphWidget:
    def __init__(self, parent_frame, theme_manager=None):
        self.parent_frame = parent_frame
        self.theme_manager = theme_manager
        self.canvas = None
        self.fig = None
        self.ax = None
        self.current_data = None
        
        # Register for theme updates if theme manager is available
        if self.theme_manager:
            self.theme_manager.register_callback(self.update_theme)
    
    def create_graph_window(self, readings, timezone_str="America/New_York", country="US"):
        """Create a separate window for the temperature graph"""
        # Create new window
        graph_window = tk.Toplevel(self.parent_frame)
        graph_window.title("📈 Temperature Trends")
        graph_window.geometry("900x600")
        
        # Apply theme colors if available
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            graph_window.configure(bg=colors["bg_primary"])
        else:
            graph_window.configure(bg="#1e40af")
        
        # Create graph in the new window
        self.render_graph(graph_window, readings, timezone_str, country)
        
        return graph_window
    
    def render_graph(self, container, readings, timezone_str="America/New_York", country="US"):
        """Render enhanced temperature graph with better styling and features"""
        if not readings:
            error_label = tk.Label(container, text="No data available for graphing", 
                                 font=("Segoe UI", 12), fg="red")
            error_label.pack(expand=True)
            return
        
        # Clear existing canvas
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        # Store current data
        self.current_data = readings
        
        # Process temperature data
        temps = []
        times = []
        
        for reading in readings:
            try:
                # Handle different data structures
                if 'temp' in reading:
                    temp = reading['temp']
                elif 'main' in reading and 'temp' in reading['main']:
                    temp = reading['main']['temp']
                else:
                    continue
                
                # Convert temperature based on country
                if country == "US":
                    temp = (temp * 9/5) + 32
                temps.append(temp)
                
                # Handle timestamp formats
                if 'timestamp' in reading:
                    time_str = reading['timestamp']
                elif 'dt_txt' in reading:
                    time_str = reading['dt_txt']
                elif 'dt' in reading:
                    # Unix timestamp
                    time_str = datetime.utcfromtimestamp(reading['dt']).isoformat()
                else:
                    continue
                
                # Parse time
                if isinstance(time_str, str):
                    if 'T' in time_str:
                        time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    else:
                        time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                else:
                    time_obj = time_str
                
                times.append(time_obj)
                
            except Exception as e:
                print(f"Error processing reading: {e}")
                continue
        
        if not temps or not times:
            error_label = tk.Label(container, text="Could not process temperature data", 
                                 font=("Segoe UI", 12), fg="red")
            error_label.pack(expand=True)
            return
        
        # Create figure with modern styling
        plt.style.use('dark_background' if self.theme_manager and self.theme_manager.is_dark_theme() else 'default')
        
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        
        # Get theme colors
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            bg_color = colors["bg_card"]
            text_color = colors["text_primary"]
            accent_color = colors["accent"]
            grid_color = colors["text_muted"]
        else:
            bg_color = "#1e3a8a"
            text_color = "white"
            accent_color = "#3b82f6"
            grid_color = "#6b7280"
        
        # Set figure and axes colors
        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        # Create temperature line with gradient effect
        line = self.ax.plot(times, temps, linewidth=3, color=accent_color, 
                           marker='o', markersize=6, markerfacecolor=accent_color,
                           markeredgecolor='white', markeredgewidth=1.5,
                           label='Temperature')[0]
        
        # Add gradient fill under the line
        self.ax.fill_between(times, temps, alpha=0.3, color=accent_color)
        
        # Add trend line if enough data points
        if len(temps) > 3:
            # Convert times to numerical values for trend calculation
            time_nums = [mdates.date2num(t) for t in times]
            z = np.polyfit(time_nums, temps, 1)
            p = np.poly1d(z)
            trend_temps = [p(t) for t in time_nums]
            
            self.ax.plot(times, trend_temps, "--", alpha=0.7, color="orange", 
                        linewidth=2, label=f'Trend ({"↗" if z[0] > 0 else "↘"})')
        
        # Enhance axes styling
        self.ax.set_title(f'Temperature Trends - Last {len(readings)} Readings', 
                         fontsize=16, fontweight='bold', color=text_color, pad=20)
        
        unit = "°F" if country == "US" else "°C"
        self.ax.set_ylabel(f'Temperature ({unit})', fontsize=12, color=text_color)
        self.ax.set_xlabel('Time', fontsize=12, color=text_color)
        
        # Format x-axis for better readability
        if len(times) > 1:
            time_span = times[-1] - times[0]
            
            if time_span.days > 2:
                self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                self.ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
            elif time_span.days > 0:
                self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            else:
                self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Rotate labels for better readability
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Style the grid
        self.ax.grid(True, alpha=0.3, color=grid_color, linestyle='-', linewidth=0.5)
        self.ax.set_axisbelow(True)
        
        # Style tick labels
        self.ax.tick_params(colors=text_color, which='both')
        
        # Add statistics box
        if temps:
            stats_text = f'Min: {min(temps):.1f}{unit}\nMax: {max(temps):.1f}{unit}\nAvg: {np.mean(temps):.1f}{unit}'
            self.ax.text(0.02, 0.98, stats_text, transform=self.ax.transAxes,
                        verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5',
                        facecolor=bg_color, alpha=0.8, edgecolor=accent_color),
                        fontsize=10, color=text_color)
        
        # Add legend
        if len(temps) > 3:  # Only show legend if we have trend line
            legend = self.ax.legend(loc='upper right', framealpha=0.9)
            legend.get_frame().set_facecolor(bg_color)
            legend.get_frame().set_edgecolor(accent_color)
            for text in legend.get_texts():
                text.set_color(text_color)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Create canvas and embed in container
        self.canvas = FigureCanvasTkAgg(self.fig, master=container)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add toolbar for interaction
        toolbar_frame = tk.Frame(container, bg=bg_color if self.theme_manager else "#1e40af")
        toolbar_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Add control buttons
        refresh_btn = tk.Button(toolbar_frame, text="🔄 Refresh", 
                               command=lambda: self.refresh_graph(),
                               bg=accent_color, fg="white", font=("Segoe UI", 9, "bold"),
                               bd=0, cursor="hand2")
        refresh_btn.pack(side='left', padx=5)
        
        export_btn = tk.Button(toolbar_frame, text="💾 Save PNG", 
                              command=lambda: self.save_graph(),
                              bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"),
                              bd=0, cursor="hand2")
        export_btn.pack(side='left', padx=5)
        
        self.canvas.draw()
    
    def update_theme(self, colors):
        """Update graph colors when theme changes"""
        if self.fig and self.ax and self.canvas:
            # Update figure colors
            self.fig.patch.set_facecolor(colors["bg_card"])
            self.ax.set_facecolor(colors["bg_card"])
            
            # Update text colors
            self.ax.title.set_color(colors["text_primary"])
            self.ax.xaxis.label.set_color(colors["text_primary"])
            self.ax.yaxis.label.set_color(colors["text_primary"])
            self.ax.tick_params(colors=colors["text_primary"])
            
            # Redraw canvas
            self.canvas.draw()
    
    def refresh_graph(self):
        """Refresh the graph with current data"""
        if self.current_data:
            self.render_graph(self.parent_frame, self.current_data)
    
    def save_graph(self):
        """Save the current graph as PNG"""
        if self.fig:
            filename = f"temperature_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.fig.savefig(filename, dpi=300, bbox_inches='tight', 
                           facecolor=self.fig.get_facecolor())
            print(f"Graph saved as {filename}")

def render_temperature_graph(parent_frame, readings, timezone_str="America/New_York", country="US", theme_manager=None):
    """Enhanced function to render temperature graph"""
    graph_widget = TemperatureGraphWidget(parent_frame, theme_manager)
    return graph_widget.create_graph_window(readings, timezone_str, country)