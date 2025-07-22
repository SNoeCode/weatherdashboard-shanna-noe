import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

def detect_trend(readings):
    """Analyze temperature trend from recent readings"""
    if len(readings) < 2:
        return "↔️ Steady", "Not enough data for trend analysis", "#FFB347"
    
    # Calculate average change over last few readings
    recent_temps = [r['temp'] for r in readings[:5]]  # Last 5 readings
    if len(recent_temps) < 2:
        return "↔️ Steady", "Insufficient data", "#FFB347"
    
    # Calculate trend
    temp_change = recent_temps[0] - recent_temps[-1]
    change_per_hour = temp_change / min(len(recent_temps), 5)
    
    if abs(change_per_hour) < 0.5:
        return "↔️ Steady", f"Temperature stable (±{abs(change_per_hour):.1f}°C/hr)", "#4CAF50"
    elif change_per_hour > 0:
        return "⬆️ Rising", f"Temperature rising by {change_per_hour:.1f}°C/hr", "#FF6B6B"
    else:
        return "⬇️ Falling", f"Temperature dropping by {abs(change_per_hour):.1f}°C/hr", "#4A90E2"

def get_trend_stats(readings):
    """Get additional trend statistics"""
    if not readings:
        return {}
    
    temps = [r['temp'] for r in readings]
    times = [datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')) for r in readings]
    
    # Calculate temperature range
    temp_range = max(temps) - min(temps)
    
    # Find hottest and coldest periods
    hottest_idx = temps.index(max(temps))
    coldest_idx = temps.index(min(temps))
    
    return {
        'temp_range': temp_range,
        'hottest_temp': max(temps),
        'coldest_temp': min(temps),
        'hottest_time': times[hottest_idx].strftime('%I:%M %p'),
        'coldest_time': times[coldest_idx].strftime('%I:%M %p'),
        'avg_temp': sum(temps) / len(temps)
    }

class TrendPanel:
    def __init__(self, parent_tab, db, logger, cfg):
        self.db = db
        self.logger = logger
        self.cfg = cfg
        self.current_city = "Knoxville"
        self.current_country = "US"
        
        # Main container with padding
        self.main_frame = ttk.Frame(parent_tab, padding=25)
        self.main_frame.pack(expand=True, fill='both')
        
        # Create header section
        self.create_header()
        
        # Create city selection
        self.create_city_selector()
        
        # Create main content area
        self.create_content_area()
        
        # Load initial data
        self.display_trend()

    def create_header(self):
        """Create attractive header section"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title with icon
        title_label = ttk.Label(
            header_frame, 
            text="📈 Weather Trend Analysis", 
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame, 
            text="Analyze temperature patterns and trends over time",
            font=("Segoe UI", 11),
            foreground="#666666"
        )
        subtitle_label.pack()

    def create_city_selector(self):
        """Create city selection section"""
        selector_frame = ttk.LabelFrame(self.main_frame, text="🌍 Location Selection", padding=15)
        selector_frame.pack(fill='x', pady=(0, 20))
        
        # City input row
        input_frame = ttk.Frame(selector_frame)
        input_frame.pack(fill='x')
        
        ttk.Label(input_frame, text="City:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="e", padx=(0, 5))
        self.city_entry = ttk.Entry(input_frame, width=20, font=("Segoe UI", 10))
        self.city_entry.grid(row=0, column=1, padx=(0, 10))
        self.city_entry.insert(0, self.current_city)
        
        ttk.Label(input_frame, text="Country:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="e", padx=(0, 5))
        self.country_entry = ttk.Entry(input_frame, width=10, font=("Segoe UI", 10))
        self.country_entry.grid(row=0, column=3, padx=(0, 10))
        self.country_entry.insert(0, self.current_country)
        
        # Analyze button
        analyze_btn = ttk.Button(
            input_frame, 
            text="🔍 Analyze Trends", 
            command=self.update_trend_analysis,
            style="Accent.TButton"
        )
        analyze_btn.grid(row=0, column=4, padx=(10, 0))

    def create_content_area(self):
        """Create main content display area"""
        # Create notebook for different views
        self.content_notebook = ttk.Notebook(self.main_frame)
        self.content_notebook.pack(expand=True, fill='both')
        
        # Trend Overview Tab
        self.trend_frame = ttk.Frame(self.content_notebook, padding=20)
        self.content_notebook.add(self.trend_frame, text="📊 Trend Overview")
        
        # Detailed Stats Tab
        self.stats_frame = ttk.Frame(self.content_notebook, padding=20)
        self.content_notebook.add(self.stats_frame, text="📋 Detailed Stats")
        
        # Create trend display sections
        self.create_trend_display()
        self.create_stats_display()

    def create_trend_display(self):
        """Create the main trend display section"""
        # Current trend card
        self.trend_card = ttk.LabelFrame(self.trend_frame, text="🎯 Current Trend", padding=20)
        self.trend_card.pack(fill='x', pady=(0, 20))
        
        # Trend indicator (will be populated dynamically)
        self.trend_indicator = ttk.Label(
            self.trend_card, 
            text="Loading...", 
            font=("Segoe UI", 24, "bold")
        )
        self.trend_indicator.pack(pady=(0, 10))
        
        # Trend description
        self.trend_description = ttk.Label(
            self.trend_card, 
            text="Analyzing temperature patterns...",
            font=("Segoe UI", 12),
            wraplength=500,
            justify="center"
        )
        self.trend_description.pack(pady=(0, 10))
        
        # Temperature summary
        self.temp_summary_frame = ttk.Frame(self.trend_card)
        self.temp_summary_frame.pack(fill='x', pady=(10, 0))

    def create_stats_display(self):
        """Create detailed statistics display"""
        # Statistics grid
        stats_container = ttk.Frame(self.stats_frame)
        stats_container.pack(expand=True, fill='both')
        
        # Temperature Range Card
        self.temp_range_card = ttk.LabelFrame(stats_container, text="🌡️ Temperature Range", padding=15)
        self.temp_range_card.grid(row=0, column=0, padx=(0, 10), pady=(0, 10), sticky="nsew")
        
        # Peak Times Card
        self.peak_times_card = ttk.LabelFrame(stats_container, text="⏰ Peak Times", padding=15)
        self.peak_times_card.grid(row=0, column=1, padx=(10, 0), pady=(0, 10), sticky="nsew")
        
        # Trend History Card
        self.trend_history_card = ttk.LabelFrame(stats_container, text="📈 Recent History", padding=15)
        self.trend_history_card.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="nsew")
        
        # Configure grid weights
        stats_container.columnconfigure(0, weight=1)
        stats_container.columnconfigure(1, weight=1)
        stats_container.rowconfigure(0, weight=1)
        stats_container.rowconfigure(1, weight=1)

    def update_trend_analysis(self):
        """Update analysis with new city data"""
        self.current_city = self.city_entry.get().strip() or "Knoxville"
        self.current_country = self.country_entry.get().strip() or "US"
        self.display_trend()

    def display_trend(self):
        """Display trend analysis for current city"""
        readings = self.db.fetch_recent(self.current_city, self.current_country, hours=24)
        
        if not readings:
            self.show_no_data_message()
            return
        
        # Get trend analysis
        trend_direction, trend_description, trend_color = detect_trend(readings)
        trend_stats = get_trend_stats(readings)
        
        # Update trend display
        self.update_trend_card(trend_direction, trend_description, trend_color)
        self.update_temperature_summary(readings, trend_stats)
        self.update_detailed_stats(trend_stats, readings)

    def update_trend_card(self, direction, description, color):
        """Update the main trend indicator card"""
        self.trend_indicator.config(text=direction, foreground=color)
        self.trend_description.config(text=description)

    def update_temperature_summary(self, readings, stats):
        """Update temperature summary section"""
        # Clear existing widgets
        for widget in self.temp_summary_frame.winfo_children():
            widget.destroy()
        
        if not stats:
            return
        
        # Current temperature
        current_temp = readings[0]['temp'] if readings else 0
        current_temp_f = (current_temp * 9/5) + 32
        
        # Create summary grid
        summary_grid = ttk.Frame(self.temp_summary_frame)
        summary_grid.pack(expand=True)
        
        # Current temperature
        current_frame = ttk.Frame(summary_grid)
        current_frame.grid(row=0, column=0, padx=20)
        ttk.Label(current_frame, text="Current", font=("Segoe UI", 9, "bold")).pack()
        ttk.Label(current_frame, text=f"{current_temp_f:.1f}°F", font=("Segoe UI", 16, "bold"), foreground="#2E7D32").pack()
        
        # Average temperature
        avg_frame = ttk.Frame(summary_grid)
        avg_frame.grid(row=0, column=1, padx=20)
        avg_temp_f = (stats['avg_temp'] * 9/5) + 32
        ttk.Label(avg_frame, text="24hr Average", font=("Segoe UI", 9, "bold")).pack()
        ttk.Label(avg_frame, text=f"{avg_temp_f:.1f}°F", font=("Segoe UI", 16, "bold"), foreground="#1976D2").pack()
        
        # Temperature range
        range_frame = ttk.Frame(summary_grid)
        range_frame.grid(row=0, column=2, padx=20)
        range_f = stats['temp_range'] * 9/5
        ttk.Label(range_frame, text="Range", font=("Segoe UI", 9, "bold")).pack()
        ttk.Label(range_frame, text=f"{range_f:.1f}°F", font=("Segoe UI", 16, "bold"), foreground="#F57C00").pack()

    def update_detailed_stats(self, stats, readings):
        """Update detailed statistics cards"""
        if not stats:
            return
        
        # Update temperature range card
        self.update_temp_range_card(stats)
        
        # Update peak times card
        self.update_peak_times_card(stats)
        
        # Update trend history card
        self.update_trend_history_card(readings)

    def update_temp_range_card(self, stats):
        """Update temperature range statistics"""
        # Clear existing widgets
        for widget in self.temp_range_card.winfo_children():
            widget.destroy()
        
        # High temperature
        high_temp_f = (stats['hottest_temp'] * 9/5) + 32
        high_frame = ttk.Frame(self.temp_range_card)
        high_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(high_frame, text="🔥 High:", font=("Segoe UI", 10, "bold")).pack(side='left')
        ttk.Label(high_frame, text=f"{high_temp_f:.1f}°F", font=("Segoe UI", 10), foreground="#D32F2F").pack(side='right')
        
        # Low temperature
        low_temp_f = (stats['coldest_temp'] * 9/5) + 32
        low_frame = ttk.Frame(self.temp_range_card)
        low_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(low_frame, text="❄️ Low:", font=("Segoe UI", 10, "bold")).pack(side='left')
        ttk.Label(low_frame, text=f"{low_temp_f:.1f}°F", font=("Segoe UI", 10), foreground="#1976D2").pack(side='right')
        
        # Range
        range_f = stats['temp_range'] * 9/5
        range_frame = ttk.Frame(self.temp_range_card)
        range_frame.pack(fill='x')
        ttk.Label(range_frame, text="📊 Range:", font=("Segoe UI", 10, "bold")).pack(side='left')
        ttk.Label(range_frame, text=f"{range_f:.1f}°F", font=("Segoe UI", 10), foreground="#388E3C").pack(side='right')

    def update_peak_times_card(self, stats):
        """Update peak times information"""
        # Clear existing widgets
        for widget in self.peak_times_card.winfo_children():
            widget.destroy()
        
        # Hottest time
        hot_frame = ttk.Frame(self.peak_times_card)
        hot_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(hot_frame, text="🌡️ Hottest:", font=("Segoe UI", 10, "bold")).pack(side='left')
        ttk.Label(hot_frame, text=stats['hottest_time'], font=("Segoe UI", 10), foreground="#D32F2F").pack(side='right')
        
        # Coldest time
        cold_frame = ttk.Frame(self.peak_times_card)
        cold_frame.pack(fill='x')
        ttk.Label(cold_frame, text="🧊 Coldest:", font=("Segoe UI", 10, "bold")).pack(side='left')
        ttk.Label(cold_frame, text=stats['coldest_time'], font=("Segoe UI", 10), foreground="#1976D2").pack(side='right')

    def update_trend_history_card(self, readings):
        """Update recent trend history"""
        # Clear existing widgets
        for widget in self.trend_history_card.winfo_children():
            widget.destroy()
        
        if len(readings) < 3:
            ttk.Label(self.trend_history_card, text="Not enough data for history", font=("Segoe UI", 10)).pack()
            return
        
        # Create scrollable history
        history_frame = ttk.Frame(self.trend_history_card)
        history_frame.pack(fill='both', expand=True)
        
        # Show last 6 readings
        for i, reading in enumerate(readings[:6]):
            if i >= 6:
                break
                
            reading_frame = ttk.Frame(history_frame)
            reading_frame.pack(fill='x', pady=2)
            
            # Time
            time_str = datetime.fromisoformat(reading['timestamp'].replace('Z', '+00:00')).strftime('%I:%M %p')
            ttk.Label(reading_frame, text=time_str, font=("Segoe UI", 9)).pack(side='left')
            
            # Temperature
            temp_f = (reading['temp'] * 9/5) + 32
            ttk.Label(reading_frame, text=f"{temp_f:.1f}°F", font=("Segoe UI", 9, "bold")).pack(side='right')
            
            # Condition
            condition = reading.get('weather_summary', 'Unknown')
            ttk.Label(reading_frame, text=condition, font=("Segoe UI", 9), foreground="#666666").pack(side='right', padx=(0, 20))

    def show_no_data_message(self):
        """Show message when no data is available"""
        # Clear all content
        for widget in self.trend_card.winfo_children():
            widget.destroy()
        
        # No data message
        no_data_frame = ttk.Frame(self.trend_card)
        no_data_frame.pack(expand=True, fill='both', pady=40)
        
        ttk.Label(no_data_frame, text="📊", font=("Segoe UI", 48)).pack(pady=(0, 10))
        ttk.Label(no_data_frame, text="No Data Available", font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(no_data_frame, text=f"No weather data found for {self.current_city}, {self.current_country}", 
                 font=("Segoe UI", 10), foreground="#666666").pack(pady=(5, 0))
        
        # Clear stats tabs
        for widget in self.temp_range_card.winfo_children():
            widget.destroy()
        for widget in self.peak_times_card.winfo_children():
            widget.destroy()
        for widget in self.trend_history_card.winfo_children():
            widget.destroy()