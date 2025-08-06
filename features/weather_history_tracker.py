import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import csv

class HistoryTracker:  
    def __init__(self, parent_tab, db):
        self.db = db
 
        self.configure_styles()
        # Main container
        self.main_container = tk.Frame(parent_tab, bg='#f0f2f5')
        self.main_container.pack(expand=True, fill='both')
        self.create_header()        
       
        self.create_control_panel()        
      
        self.create_graph_section()        
       
        self.create_data_table()       

        self.create_statistics_section()
        
        # Load initial data
        self.load_data()
    
    def configure_styles(self):
        style = ttk.Style()
        
        # Configure styles
        style.configure("Header.TFrame", background="#34495e")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("Modern.TFrame", background="#f0f2f5")
        
        style.configure("Header.TLabel", background="#34495e", foreground="#ffffff", 
                       font=("Segoe UI", 16, "bold"))
        style.configure("Title.TLabel", background="#f0f2f5", foreground="#2c3e50", 
                       font=("Segoe UI", 14, "bold"))
        style.configure("Card.TLabel", background="#ffffff", foreground="#2c3e50", 
                       font=("Segoe UI", 11))
        
        style.configure("Modern.TButton", font=("Segoe UI", 10), padding=8)
        style.configure("Modern.TCombobox", font=("Segoe UI", 10))
        
        style.configure("Treeview", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    
    def create_header(self):
        header_frame = tk.Frame(self.main_container, bg='#34495e', height=80)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header_frame, bg='#34495e')
        header_content.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Title
        title_label = tk.Label(header_content, text="📊 Weather History & Analytics", 
                              bg='#34495e', fg='#ffffff', 
                              font=("Segoe UI", 20, "bold"))
        title_label.pack(side='left', anchor='w')
        
        # Subtitle
        subtitle_label = tk.Label(header_content, text="Track temperature trends and weather patterns", 
                                 bg='#34495e', fg='#bdc3c7', 
                                 font=("Segoe UI", 12))
        subtitle_label.pack(side='left', anchor='w', padx=(20, 0))
    
    def create_control_panel(self):
        """Create control panel for filtering and options"""
        control_frame = tk.Frame(self.main_container, bg='#ffffff', relief='flat', bd=1)
        control_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Control header
        control_header = tk.Frame(control_frame, bg='#ffffff')
        control_header.pack(fill='x', padx=20, pady=(15, 10))
        
        control_title = tk.Label(control_header, text="⚙️ Display Options", 
                                bg='#ffffff', fg='#2c3e50', 
                                font=("Segoe UI", 14, "bold"))
        control_title.pack(side='left')
        
        # Control options
        options_frame = tk.Frame(control_frame, bg='#ffffff')
        options_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        # Time range selector
        time_frame = tk.Frame(options_frame, bg='#ffffff')
        time_frame.pack(side='left', padx=(0, 30))
        
        tk.Label(time_frame, text="Time Range:", bg='#ffffff', fg='#2c3e50', 
                font=("Segoe UI", 10, "bold")).pack(anchor='w')
        
        self.time_range_var = tk.StringVar(value="7 days")
        time_combo = ttk.Combobox(time_frame, textvariable=self.time_range_var, 
                                 values=["24 hours", "7 days", "30 days", "90 days", "All time"],
                                 state="readonly", width=12)
        time_combo.pack(pady=(5, 0))
        time_combo.bind("<<ComboboxSelected>>", self.on_time_range_change)
        
        # Graph type selector
        graph_frame = tk.Frame(options_frame, bg='#ffffff')
        graph_frame.pack(side='left', padx=(0, 30))
        
        tk.Label(graph_frame, text="Graph Type:", bg='#ffffff', fg='#2c3e50', 
                font=("Segoe UI", 10, "bold")).pack(anchor='w')
        
        self.graph_type_var = tk.StringVar(value="Line")
        graph_combo = ttk.Combobox(graph_frame, textvariable=self.graph_type_var,
                                  values=["Line", "Bar", "Scatter", "Area"],
                                  state="readonly", width=12)
        graph_combo.pack(pady=(5, 0))
        graph_combo.bind("<<ComboboxSelected>>", self.on_graph_type_change)
        
        # Temperature unit selector
        unit_frame = tk.Frame(options_frame, bg='#ffffff')
        unit_frame.pack(side='left', padx=(0, 30))
        
        tk.Label(unit_frame, text="Temperature Unit:", bg='#ffffff', fg='#2c3e50', 
                font=("Segoe UI", 10, "bold")).pack(anchor='w')
        
        self.temp_unit_var = tk.StringVar(value="Fahrenheit")
        unit_combo = ttk.Combobox(unit_frame, textvariable=self.temp_unit_var,
                                 values=["Celsius", "Fahrenheit"],
                                 state="readonly", width=12)
        unit_combo.pack(pady=(5, 0))
        unit_combo.bind("<<ComboboxSelected>>", self.on_unit_change)
        
        # Refresh button
        refresh_btn = tk.Button(options_frame, text="🔄 Refresh Data", 
                               bg='#3498db', fg='#ffffff', 
                               font=("Segoe UI", 10, "bold"), 
                               relief='flat', bd=0, padx=20, pady=8,
                               cursor='hand2',
                               command=self.load_data)
        refresh_btn.pack(side='right', pady=(20, 0))
        
        # Export button
        export_btn = tk.Button(options_frame, text="📊 Export Data", 
                              bg='#27ae60', fg='#ffffff', 
                              font=("Segoe UI", 10, "bold"), 
                              relief='flat', bd=0, padx=20, pady=8,
                              cursor='hand2',
                              command=self.export_data)
        export_btn.pack(side='right', padx=(0, 10), pady=(20, 0))
        
    def create_graph_section(self):
        graph_frame = tk.Frame(self.main_container, bg='#ffffff', relief='flat', bd=1)
        graph_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Graph header
        graph_header = tk.Frame(graph_frame, bg='#ffffff')
        graph_header.pack(fill='x', padx=20, pady=(15, 10))
        
        graph_title = tk.Label(graph_header, text="🌡️ Temperature Trends", 
                              bg='#ffffff', fg='#2c3e50', 
                              font=("Segoe UI", 14, "bold"))
        graph_title.pack(side='left')
        
        # Graph canvas container
        self.graph_container = tk.Frame(graph_frame, bg='#ffffff')
        self.graph_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Initialize matplotlib figure
        self.fig = Figure(figsize=(12, 6), dpi=100, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.graph_container)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def create_data_table(self):
        table_frame = tk.Frame(self.main_container, bg='#ffffff', relief='flat', bd=1)
        table_frame.pack(fill='x', padx=20, pady=(0, 20))        
     
        table_header = tk.Frame(table_frame, bg='#ffffff')
        table_header.pack(fill='x', padx=20, pady=(15, 10))
        
        table_title = tk.Label(table_header, text="📋 Weather Data Records", 
                              bg='#ffffff', fg='#2c3e50', 
                              font=("Segoe UI", 14, "bold"))
        table_title.pack(side='left')
        
        # Create treeview with scrollbar
        table_container = tk.Frame(table_frame, bg='#ffffff')
        table_container.pack(fill='x', padx=20, pady=(0, 20))
        
        # Define columns
        columns = ("Date", "Time", "Temperature", "Condition", "Humidity", "Wind Speed")
        
        self.tree = ttk.Treeview(table_container, columns=columns, show='headings', height=8)
        
        # Define headings
        self.tree.heading("Date", text="Date")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Temperature", text="Temperature")
        self.tree.heading("Condition", text="Condition")
        self.tree.heading("Humidity", text="Humidity %")
        self.tree.heading("Wind Speed", text="Wind Speed")
        
        # Configure column widths
        self.tree.column("Date", width=100)
        self.tree.column("Time", width=80)
        self.tree.column("Temperature", width=100)
        self.tree.column("Condition", width=150)
        self.tree.column("Humidity", width=100)
        self.tree.column("Wind Speed", width=100)
        
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack table and scrollbar
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def create_statistics_section(self):
        """Create statistics section"""
        stats_frame = tk.Frame(self.main_container, bg='#ffffff', relief='flat', bd=1)
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        stats_header = tk.Frame(stats_frame, bg='#ffffff')
        stats_header.pack(fill='x', padx=20, pady=(15, 10))
        
        stats_title = tk.Label(stats_header, text="📈 Temperature Statistics", 
                              bg='#ffffff', fg='#2c3e50', 
                              font=("Segoe UI", 14, "bold"))
        stats_title.pack(side='left')
        
        # Statistics grid
        self.stats_container = tk.Frame(stats_frame, bg='#ffffff')
        self.stats_container.pack(fill='x', padx=20, pady=(0, 20))
        
        self.create_stat_cards()
    
    def create_stat_cards(self):
        # Clear existing cards
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        stats_data = [
            ("🌡️ Average Temp", "72.5°F", "#e74c3c"),
            ("⬆️ Highest Temp", "89.2°F", "#f39c12"),
            ("⬇️ Lowest Temp", "45.1°F", "#3498db"),
            ("📊 Data Points", "156", "#27ae60"),
            ("📅 Date Range", "30 days", "#9b59b6"),
            ("🌤️ Most Common", "Sunny", "#f1c40f")
        ]
        
        # Create cards in grid
        for i, (label, value, color) in enumerate(stats_data):
            card = tk.Frame(self.stats_container, bg=color, relief='flat', bd=1)
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky='ew')
                       
            self.stats_container.grid_columnconfigure(i%3, weight=1)
                      
            card_content = tk.Frame(card, bg=color)
            card_content.pack(fill='both', expand=True, padx=15, pady=15)
                    
            value_label = tk.Label(card_content, text=value, 
                                  bg=color, fg='#ffffff', 
                                  font=("Segoe UI", 16, "bold"))
            value_label.pack()            
          
            desc_label = tk.Label(card_content, text=label, 
                                 bg=color, fg='#ffffff', 
                                 font=("Segoe UI", 10))
            desc_label.pack()
    
    def load_data(self):
        try:
            # Get time range
            time_range = self.time_range_var.get()
            
            # Calculate date range
            end_date = datetime.now()
            if time_range == "24 hours":
                start_date = end_date - timedelta(hours=24)
            elif time_range == "7 days":
                start_date = end_date - timedelta(days=7)
            elif time_range == "30 days":
                start_date = end_date - timedelta(days=30)
            elif time_range == "90 days":
                start_date = end_date - timedelta(days=90)
            else:  
                start_date = datetime(2020, 1, 1)            
            
            data = self.fetch_weather_data(start_date, end_date)
                        
            self.update_graph(data)            
         
            self.update_table(data)            
           
            self.update_statistics(data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def fetch_weather_data(self, start_date, end_date):      
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Query data
            query = """
                SELECT timestamp, temperature, weather_summary, humidity, wind_speed
                FROM weather_data 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """
            
            cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
            data = cursor.fetchall()
            
            conn.close()
            
            return data
            
        except Exception as e:
            print(f"Database error: {e}")
            return self.generate_sample_data()
    
    def generate_sample_data(self):
       
        data = []
        base_date = datetime.now() - timedelta(days=7)
        
        for i in range(168):  # 7 days * 24 hours
            timestamp = base_date + timedelta(hours=i)
            temp = 20 + 10 * np.sin(i * np.pi / 12) + np.random.normal(0, 2)
            condition = np.random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"])
            humidity = np.random.randint(30, 80)
            wind_speed = np.random.randint(5, 25)
            
            data.append((timestamp.isoformat(), temp, condition, humidity, wind_speed))
        
        return data
    
    def update_graph(self, data):
        if not data:
            return
        
        # Clear previous plot
        self.ax.clear()
        
        timestamps = [datetime.fromisoformat(row[0]) for row in data]
        temperatures = [float(row[1]) for row in data]
        
        # Convert temperature if needed
        if self.temp_unit_var.get() == "Fahrenheit":
            temperatures = [(temp) for temp in temperatures]
            unit = "°F"
        else:
            unit = "°C"
       

        timestamps = np.array(timestamps)
        temperatures = np.array(temperatures)

        # Plot based on graph type
        graph_type = self.graph_type_var.get()
        
        if graph_type == "Line":
            self.ax.plot(timestamps, temperatures, linewidth=2, color='#3498db', marker='o', markersize=3)
        elif graph_type == "Bar":
            self.ax.bar(timestamps, temperatures, color='#3498db', alpha=0.7)
        elif graph_type == "Scatter":
            self.ax.scatter(timestamps, temperatures, color='#3498db', alpha=0.7)
        elif graph_type == "Area":
            self.ax.fill_between(timestamps, temperatures, alpha=0.3, color='#3498db')
            self.ax.plot(timestamps, temperatures, color='#3498db', linewidth=2)
        
        # Customize plot
        self.ax.set_xlabel('Time', fontsize=12)
        self.ax.set_ylabel(f'Temperature ({unit})', fontsize=12)
        self.ax.set_title(f'Temperature Trends - {self.time_range_var.get()}', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
        # Format x-axis
        self.fig.autofmt_xdate()
        
        # Add trend line for line graphs
        if graph_type == "Line" and len(timestamps) > 1:
            z = np.polyfit(range(len(temperatures)), temperatures, 1)
            p = np.poly1d(z)
            self.ax.plot(timestamps, p(range(len(temperatures))), 
                        "--", color='#e74c3c', alpha=0.8, linewidth=2, label='Trend')
            self.ax.legend()
        
            self.fig.tight_layout()
        
        # Refresh canvas
        self.canvas.draw()
    
    def update_table(self, data):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add new data
        for row in data[-50:]:  # Show last 50 records
            timestamp = datetime.fromisoformat(row[0])
            date_str = timestamp.strftime("%Y-%m-%d")
            time_str = timestamp.strftime("%H:%M")
            
       
            temp = float(row[1])
            if self.temp_unit_var.get() == "Fahrenheit":
                temp = (temp)
                temp_str = f"{temp:.1f}°F"
            else:
                temp_str = f"{temp:.1f}°C"
            
            condition = row[2]
            humidity = f"{row[3]}%" if row[3] else "N/A"
            wind_speed = f"{row[4]} mph" if row[4] else "N/A"
            
            self.tree.insert("", "end", values=(date_str, time_str, temp_str, condition, humidity, wind_speed))
    
    def update_statistics(self, data):
        if not data:
            return
        
        # Calculate statistics
        temperatures = [float(row[1]) for row in data]
        
        if self.temp_unit_var.get() == "Fahrenheit":
            temperatures = [(temp) for temp in temperatures]
            unit = "°F"
        else:
            unit = "°C"
        
        avg_temp = np.mean(temperatures)
        max_temp = np.max(temperatures)
        min_temp = np.min(temperatures)
        data_points = len(data)
        
        # Most common condition
        conditions = [row[2] for row in data]
        most_common = max(set(conditions), key=conditions.count) if conditions else "N/A"
        
        # Update statistics
        stats_data = [
            ("🌡️ Average Temp", f"{avg_temp:.1f}{unit}", "#e74c3c"),
            ("⬆️ Highest Temp", f"{max_temp:.1f}{unit}", "#f39c12"),
            ("⬇️ Lowest Temp", f"{min_temp:.1f}{unit}", "#3498db"),
            ("📊 Data Points", str(data_points), "#27ae60"),
            ("📅 Date Range", self.time_range_var.get(), "#9b59b6"),
            ("🌤️ Most Common", most_common, "#f1c40f")
        ]
       
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        # Create new cards
        for i, (label, value, color) in enumerate(stats_data):
            card = tk.Frame(self.stats_container, bg=color, relief='flat', bd=1)
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky='ew')
            
            self.stats_container.grid_columnconfigure(i%3, weight=1)
            
            # Card content
            card_content = tk.Frame(card, bg=color)
            card_content.pack(fill='both', expand=True, padx=15, pady=15)
            
            # Value label
            value_label = tk.Label(card_content, text=value, 
                                  bg=color, fg='#ffffff', 
                                  font=("Segoe UI", 16, "bold"))
            value_label.pack()
            
            # Description label
            desc_label = tk.Label(card_content, text=label, 
                                 bg=color, fg='#ffffff', 
                                 font=("Segoe UI", 10))
            desc_label.pack()
    
    def on_time_range_change(self, event):
      
        self.load_data()
    
    def on_graph_type_change(self, event):
      
        self.load_data()
    
    def on_unit_change(self, event):      
        self.load_data()
    
    def export_data(self):
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                # Get current data
                time_range = self.time_range_var.get()
                end_date = datetime.now()
                
                if time_range == "24 hours":
                    start_date = end_date - timedelta(hours=24)
                elif time_range == "7 days":
                    start_date = end_date - timedelta(days=7)
                elif time_range == "30 days":
                    start_date = end_date - timedelta(days=30)
                elif time_range == "90 days":
                    start_date = end_date - timedelta(days=90)
                else:
                    start_date = datetime(2020, 1, 1)
                
                data = self.fetch_weather_data(start_date, end_date)
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Timestamp', 'Temperature', 'Condition', 'Humidity', 'Wind Speed'])
                    writer.writerows(data)
                
                messagebox.showinfo("Success", f"Data exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
