import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from features.simple_statisitics import get_weather_stats
from features.weather_icons import get_icon_path
from datetime import datetime
import threading

class CityComparisonPanel:
    def __init__(self, parent_tab, fetcher, db, logger):
        self.fetcher = fetcher
        self.db = db
        self.logger = logger
        self.comparison_data = {}
        
        # Main container with padding
        self.main_frame = ttk.Frame(parent_tab, padding=25)
        self.main_frame.pack(expand=True, fill='both')
        
        # Create header
        self.create_header()
        
        # Create input section
        self.create_input_section()
        
        # Create comparison display
        self.create_comparison_display()
        
        # Create detailed comparison
        self.create_detailed_comparison()

    def create_header(self):
        """Create attractive header section"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill='x', pady=(0, 25))
        
        # Title with icon
        title_label = ttk.Label(
            header_frame, 
            text="🆚 City Weather Comparison", 
            font=("Segoe UI", 22, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame, 
            text="Compare current weather conditions and statistics between two cities",
            font=("Segoe UI", 12),
            foreground="#666666"
        )
        subtitle_label.pack()

    def create_input_section(self):
        """Create city input section"""
        input_frame = ttk.LabelFrame(self.main_frame, text="🌍 Select Cities to Compare", padding=20)
        input_frame.pack(fill='x', pady=(0, 25))
        
        # Create grid for inputs
        grid_frame = ttk.Frame(input_frame)
        grid_frame.pack(expand=True)
        
        # City A section
        city_a_frame = ttk.LabelFrame(grid_frame, text="🌆 City A", padding=15)
        city_a_frame.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        
        ttk.Label(city_a_frame, text="City Name:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        self.city1_entry = ttk.Entry(city_a_frame, width=25, font=("Segoe UI", 11))
        self.city1_entry.pack(fill='x', pady=(2, 10))
        self.city1_entry.insert(0, "Knoxville")
        
        ttk.Label(city_a_frame, text="Country Code:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        self.country1_entry = ttk.Entry(city_a_frame, width=25, font=("Segoe UI", 11))
        self.country1_entry.pack(fill='x', pady=(2, 0))
        self.country1_entry.insert(0, "US")
        
        # VS label
        vs_frame = ttk.Frame(grid_frame)
        vs_frame.grid(row=0, column=1, padx=15)
        ttk.Label(vs_frame, text="VS", font=("Segoe UI", 20, "bold"), foreground="#FF6B6B").pack(pady=40)
        
        # City B section
        city_b_frame = ttk.LabelFrame(grid_frame, text="🏙️ City B", padding=15)
        city_b_frame.grid(row=0, column=2, padx=(15, 0), sticky="nsew")
        
        ttk.Label(city_b_frame, text="City Name:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        self.city2_entry = ttk.Entry(city_b_frame, width=25, font=("Segoe UI", 11))
        self.city2_entry.pack(fill='x', pady=(2, 10))
        self.city2_entry.insert(0, "Nashville")
        
        ttk.Label(city_b_frame, text="Country Code:", font=("Segoe UI", 10, "bold")).pack(anchor='w')
        self.country2_entry = ttk.Entry(city_b_frame, width=25, font=("Segoe UI", 11))
        self.country2_entry.pack(fill='x', pady=(2, 0))
        self.country2_entry.insert(0, "US")
        
        # Configure grid weights
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(2, weight=1)
        
        # Compare button
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        self.compare_button = ttk.Button(
            button_frame, 
            text="🔍 Compare Cities", 
            command=self.compare_cities_threaded,
            style="Accent.TButton"
        )
        self.compare_button.pack(expand=True)
        
        # Loading indicator
        self.loading_label = ttk.Label(button_frame, text="", font=("Segoe UI", 10))
        self.loading_label.pack(pady=(10, 0))

    def create_comparison_display(self):
        """Create main comparison display area"""
        self.comparison_frame = ttk.LabelFrame(self.main_frame, text="📊 Weather Comparison", padding=20)
        self.comparison_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Initially show welcome message
        self.show_welcome_message()

    def create_detailed_comparison(self):
        """Create detailed comparison section"""
        self.details_frame = ttk.LabelFrame(self.main_frame, text="📋 Detailed Analysis", padding=20)
        self.details_frame.pack(fill='x')
        
        # Initially hidden
        self.details_frame.pack_forget()

    def show_welcome_message(self):
        """Show welcome message before comparison"""
        welcome_frame = ttk.Frame(self.comparison_frame)
        welcome_frame.pack(expand=True, fill='both')
        
        ttk.Label(welcome_frame, text="🌤️", font=("Segoe UI", 72)).pack(pady=(50, 20))
        ttk.Label(welcome_frame, text="Ready to Compare Cities", font=("Segoe UI", 18, "bold")).pack()
        ttk.Label(welcome_frame, text="Enter two cities above and click 'Compare Cities' to see the weather comparison", 
                 font=("Segoe UI", 11), foreground="#666666").pack(pady=(10, 0))

    def compare_cities_threaded(self):
        """Start comparison in separate thread"""
        threading.Thread(target=self.compare_cities, daemon=True).start()

    def compare_cities(self):
        """Compare weather between two cities"""
        # Update UI to show loading
        self.root_after_idle(self.show_loading)
        
        city_a = self.city1_entry.get().strip()
        city_b = self.city2_entry.get().strip()
        country_a = self.country1_entry.get().strip() or "US"
        country_b = self.country2_entry.get().strip() or "US"

        if not city_a or not city_b:
            self.root_after_idle(lambda: messagebox.showwarning("Missing Input", "Please enter both cities."))
            self.root_after_idle(self.hide_loading)
            return

        try:
            # Fetch weather data
            data_a = self.fetcher.fetch_current_weather(city_a, country_a)
            data_b = self.fetcher.fetch_current_weather(city_b, country_b)

            if not data_a or not data_b:
                self.root_after_idle(lambda: messagebox.showerror("❌ Compare Error", "Could not fetch weather for one or both cities."))
                self.root_after_idle(self.hide_loading)
                return

            # Get statistics
            stats_a = get_weather_stats(self.db, data_a["city"], data_a["country"])
            stats_b = get_weather_stats(self.db, data_b["city"], data_b["country"])

            # Store data for later use
            self.comparison_data = {
                'city_a': {'data': data_a, 'stats': stats_a},
                'city_b': {'data': data_b, 'stats': stats_b}
            }

            # Update UI with results
            self.root_after_idle(self.display_comparison_results)
            
        except Exception as e:
            self.logger.error(f"Error in city comparison: {e}")
            self.root_after_idle(lambda: messagebox.showerror("Error", f"Comparison failed: {str(e)}"))
            self.root_after_idle(self.hide_loading)

    def root_after_idle(self, func):
        """Helper to execute function on main thread"""
        self.main_frame.after_idle(func)

    def show_loading(self):
        """Show loading indicator"""
        self.compare_button.config(state='disabled')
        self.loading_label.config(text="🔄 Fetching weather data...")
        
        # Clear comparison frame
        for widget in self.comparison_frame.winfo_children():
            widget.destroy()
        
        loading_frame = ttk.Frame(self.comparison_frame)
        loading_frame.pack(expand=True, fill='both')
        
        ttk.Label(loading_frame, text="🔄", font=("Segoe UI", 48)).pack(pady=(50, 10))
        ttk.Label(loading_frame, text="Loading Comparison...", font=("Segoe UI", 14, "bold")).pack()

    def hide_loading(self):
        """Hide loading indicator"""
        self.compare_button.config(state='normal')
        self.loading_label.config(text="")

    def display_comparison_results(self):
        """Display the comparison results"""
        self.hide_loading()
        
        # Clear comparison frame
        for widget in self.comparison_frame.winfo_children():
            widget.destroy()
        
        if not self.comparison_data:
            return
        
        # Create comparison layout
        comparison_container = ttk.Frame(self.comparison_frame)
        comparison_container.pack(expand=True, fill='both')
        
        # Create weather cards
        self.create_weather_cards(comparison_container)
        
        # Show detailed comparison
        self.show_detailed_comparison()

    def create_weather_cards(self, container):
        """Create weather cards for both cities"""
        # City A Card
        city_a_data = self.comparison_data['city_a']
        city_a_card = self.create_city_card(container, city_a_data, "City A", 0)
        
        # Comparison indicators
        self.create_comparison_indicators(container)
        
        # City B Card
        city_b_data = self.comparison_data['city_b']
        city_b_card = self.create_city_card(container, city_b_data, "City B", 2)
        
        # Configure grid weights
        container.columnconfigure(0, weight=1)
        container.columnconfigure(2, weight=1)

