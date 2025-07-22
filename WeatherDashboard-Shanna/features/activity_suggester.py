import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def suggest_activity(temp, condition):
    """
    Enhanced activity suggestions based on temperature and weather conditions
    
    Args:
        temp (float): Temperature in Celsius
        condition (str): Weather condition description
        
    Returns:
        str: Activity suggestion with appropriate emoji
    """
    condition_lower = condition.lower()
    temp_f = (temp * 9/5) + 32  # Convert to Fahrenheit for easier reading
    
    # Weather-based suggestions
    if any(word in condition_lower for word in ["rain", "drizzle", "shower"]):
        return "☔ Perfect for indoor activities - read a book, cook, or watch movies!"
    elif any(word in condition_lower for word in ["snow", "blizzard", "ice"]):
        return "❄️ Winter wonderland! Build a snowman or enjoy hot cocoa inside!"
    elif any(word in condition_lower for word in ["storm", "thunder", "lightning"]):
        return "⚡ Stay safe indoors - great time for board games or creative projects!"
    elif any(word in condition_lower for word in ["fog", "mist", "haze"]):
        return "🌫️ Limited visibility - perfect for indoor workout or meditation!"
    
    # Temperature-based suggestions
    if temp_f < 32:  # Below freezing
        return "🧊 Bundle up! Perfect for winter sports or cozy indoor activities!"
    elif temp_f < 50:  # Cold
        return "🧥 Chilly day - great for brisk walks, shopping, or museum visits!"
    elif temp_f < 70:  # Cool/Mild
        return "🍂 Perfect weather for hiking, cycling, or outdoor photography!"
    elif temp_f < 80:  # Comfortable
        return "🌞 Beautiful day! Ideal for picnics, gardening, or outdoor sports!"
    elif temp_f < 90:  # Warm
        return "🏖️ Great beach weather! Swimming, barbecue, or park activities!"
    else:  # Hot
        return "🌡️ Stay cool! Early morning walks, indoor activities, or pool time!"

def get_activity_color(temp, condition):
    """
    Get appropriate color for activity suggestion based on conditions
    
    Args:
        temp (float): Temperature in Celsius
        condition (str): Weather condition
        
    Returns:
        str: Hex color code
    """
    condition_lower = condition.lower()
    
    if any(word in condition_lower for word in ["rain", "storm", "snow"]):
        return "#64748b"  # Gray for weather warnings
    elif temp < 0:
        return "#3b82f6"  # Blue for cold
    elif temp < 20:
        return "#10b981"  # Green for mild
    elif temp < 30:
        return "#f59e0b"  # Yellow for warm
    else:
        return "#ef4444"  # Red for hot

class ActivityPanel:
    """Enhanced activity panel with better styling and more features"""
    
    def __init__(self, parent_tab, fetcher, db):
        self.fetcher = fetcher
        self.db = db
        
        # Configure modern styles
        self.configure_styles()
        
        # Main container with gradient background
        self.main_container = tk.Frame(parent_tab, bg='#f0f2f5')
        self.main_container.pack(expand=True, fill='both')
        
        # Create scrollable frame
        self.create_scrollable_frame()
        
        # Header section
        self.create_header()
        
        # Weather and location section
        self.create_weather_section()
        
        # Activity suggestions section
        self.create_activity_section()
        
        # Additional options section
        self.create_options_section()
        
        # Auto-load suggestions for default city
        self.main_container.after(100, self.update_suggestions)
    
    def configure_styles(self):
        """Configure modern UI styles"""
        style = ttk.Style()
        
        # Configure modern frame styles
        style.configure("Header.TFrame", background="#2c3e50")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("Modern.TFrame", background="#f0f2f5")
        
        # Configure label styles
        style.configure("Header.TLabel", background="#2c3e50", foreground="#ffffff", 
                       font=("Segoe UI", 16, "bold"))
        style.configure("Title.TLabel", background="#f0f2f5", foreground="#2c3e50", 
                       font=("Segoe UI", 14, "bold"))
        style.configure("Card.TLabel", background="#ffffff", foreground="#2c3e50", 
                       font=("Segoe UI", 11))
        style.configure("Weather.TLabel", background="#ffffff", foreground="#34495e", 
                       font=("Segoe UI", 12, "bold"))
        
        # Configure button styles
        style.configure("Modern.TButton", font=("Segoe UI", 10), padding=10)
        style.configure("Activity.TButton", font=("Segoe UI", 10), padding=8)
        
        # Configure entry styles
        style.configure("Modern.TEntry", font=("Segoe UI", 10), padding=5)
        
        # Configure labelframe styles
        style.configure("Card.TLabelframe", background="#ffffff", foreground="#2c3e50",
                       font=("Segoe UI", 11, "bold"))
        style.configure("Card.TLabelframe.Label", background="#ffffff", foreground="#2c3e50",
                       font=("Segoe UI", 11, "bold"))
    
    def create_scrollable_frame(self):
        """Create a scrollable frame for content"""
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_container, bg='#f0f2f5', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#f0f2f5')
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_header(self):
        """Create modern header section"""
        header_frame = tk.Frame(self.scrollable_frame, bg='#2c3e50', height=80)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(expand=True, fill='both', padx=30, pady=20)
        
        # Title with emoji
        title_label = tk.Label(header_content, text="🎯 Activity Suggestions", 
                              bg='#2c3e50', fg='#ffffff', 
                              font=("Segoe UI", 20, "bold"))
        title_label.pack(side='left', anchor='w')
        
        # Subtitle
        subtitle_label = tk.Label(header_content, text="Find the perfect activity for today's weather", 
                                 bg='#2c3e50', fg='#bdc3c7', 
                                 font=("Segoe UI", 12))
        subtitle_label.pack(side='left', anchor='w', padx=(20, 0))
    
    def create_weather_section(self):
        """Create weather information section"""
        weather_frame = tk.Frame(self.scrollable_frame, bg='#ffffff', relief='flat', bd=1)
        weather_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Weather header
        weather_header = tk.Frame(weather_frame, bg='#ffffff', height=50)
        weather_header.pack(fill='x', padx=20, pady=(15, 0))
        weather_header.pack_propagate(False)
        
        weather_title = tk.Label(weather_header, text="📍 Location & Weather", 
                                bg='#ffffff', fg='#2c3e50', 
                                font=("Segoe UI", 14, "bold"))
        weather_title.pack(side='left', anchor='w', pady=10)
        
        # Location input section
        location_frame = tk.Frame(weather_frame, bg='#ffffff')
        location_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        # City input
        city_frame = tk.Frame(location_frame, bg='#ffffff')
        city_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(city_frame, text="City:", bg='#ffffff', fg='#2c3e50', 
                font=("Segoe UI", 10)).pack(anchor='w')
        self.city_entry = tk.Entry(city_frame, font=("Segoe UI", 10), width=15, 
                                  relief='flat', bd=1, bg='#f8f9fa')
        self.city_entry.pack(pady=(5, 0))
        self.city_entry.insert(0, "Knoxville")
        
        # Country input
        country_frame = tk.Frame(location_frame, bg='#ffffff')
        country_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(country_frame, text="Country:", bg='#ffffff', fg='#2c3e50', 
                font=("Segoe UI", 10)).pack(anchor='w')
        self.country_entry = tk.Entry(country_frame, font=("Segoe UI", 10), width=8, 
                                     relief='flat', bd=1, bg='#f8f9fa')
        self.country_entry.pack(pady=(5, 0))
        self.country_entry.insert(0, "US")
        
        # Update button
        update_btn = tk.Button(location_frame, text="🔍 Update Weather", 
                              bg='#3498db', fg='#ffffff', 
                              font=("Segoe UI", 10, "bold"), 
                              relief='flat', bd=0, padx=20, pady=8,
                              cursor='hand2',
                              command=self.update_suggestions)
        update_btn.pack(side='left', pady=(20, 0))
        
        # Weather display area
        self.weather_display = tk.Frame(weather_frame, bg='#ffffff')
        self.weather_display.pack(fill='x', padx=20, pady=(0, 20))
    
    def create_activity_section(self):
        """Create main activity suggestions section"""
        activity_frame = tk.Frame(self.scrollable_frame, bg='#ffffff', relief='flat', bd=1)
        activity_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Activity header
        activity_header = tk.Frame(activity_frame, bg='#ffffff', height=50)
        activity_header.pack(fill='x', padx=20, pady=(15, 0))
        activity_header.pack_propagate(False)
        
        activity_title = tk.Label(activity_header, text="🎯 Today's Activity Recommendations", 
                                 bg='#ffffff', fg='#2c3e50', 
                                 font=("Segoe UI", 14, "bold"))
        activity_title.pack(side='left', anchor='w', pady=10)
        
        # Main suggestion display
        self.main_suggestion_frame = tk.Frame(activity_frame, bg='#ffffff')
        self.main_suggestion_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.suggestion_label = tk.Label(self.main_suggestion_frame, 
                                        text="Click 'Update Weather' to see activity recommendations",
                                        bg='#ffffff', fg='#7f8c8d', 
                                        font=("Segoe UI", 12),
                                        wraplength=600,
                                        justify="center")
        self.suggestion_label.pack(pady=20)
    
    def create_options_section(self):
        """Create alternative activity options section"""
        options_frame = tk.Frame(self.scrollable_frame, bg='#ffffff', relief='flat', bd=1)
        options_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Options header
        options_header = tk.Frame(options_frame, bg='#ffffff', height=50)
        options_header.pack(fill='x', padx=20, pady=(15, 0))
        options_header.pack_propagate(False)
        
        options_title = tk.Label(options_header, text="🎨 Alternative Activities", 
                                bg='#ffffff', fg='#2c3e50', 
                                font=("Segoe UI", 14, "bold"))
        options_title.pack(side='left', anchor='w', pady=10)
        
        # Options display area
        self.options_display = tk.Frame(options_frame, bg='#ffffff')
        self.options_display.pack(fill='x', padx=20, pady=(0, 20))
    
    def update_suggestions(self):
        """Update activity suggestions based on current weather"""
        city = self.city_entry.get().strip() or "Knoxville"
        country = self.country_entry.get().strip() or "US"
        
        # Clear previous displays
        for widget in self.weather_display.winfo_children():
            widget.destroy()
        for widget in self.main_suggestion_frame.winfo_children():
            widget.destroy()
        for widget in self.options_display.winfo_children():
            widget.destroy()
        
        # Show loading message
        loading_label = tk.Label(self.weather_display, text="🔄 Loading weather data...", 
                               bg='#ffffff', fg='#7f8c8d', 
                               font=("Segoe UI", 11))
        loading_label.pack(pady=10)
        
        # Update display
        self.scrollable_frame.update()
        
        # Fetch current weather
        try:
            weather_data = self.fetcher.fetch_current_weather(city, country)
            
            if weather_data:
                # Clear loading message
                loading_label.destroy()
                
                # Display weather information
                self.display_weather_info(weather_data, city, country)
                
                # Display main activity suggestion
                self.display_main_suggestion(weather_data)
                
                # Display alternative activities
                self.display_alternative_activities(weather_data)
                
            else:
                loading_label.config(text="❌ Could not fetch weather data. Please check your connection.")
                
        except Exception as e:
            loading_label.config(text=f"❌ Error: {str(e)}")
    
    def display_weather_info(self, weather_data, city, country):
        """Display current weather information"""
        temp_f = (weather_data['temp'] * 9/5) + 32
        condition = weather_data['weather_summary']
        
        # Weather info container
        weather_info = tk.Frame(self.weather_display, bg='#f8f9fa', relief='flat', bd=1)
        weather_info.pack(fill='x', pady=10)
        
        # Location and temperature
        location_temp = tk.Frame(weather_info, bg='#f8f9fa')
        location_temp.pack(fill='x', padx=15, pady=15)
        
        location_label = tk.Label(location_temp, text=f"📍 {city}, {country}", 
                                 bg='#f8f9fa', fg='#2c3e50', 
                                 font=("Segoe UI", 14, "bold"))
        location_label.pack(side='left')
        
        temp_label = tk.Label(location_temp, text=f"🌡️ {temp_f:.1f}°F", 
                             bg='#f8f9fa', fg='#e74c3c', 
                             font=("Segoe UI", 14, "bold"))
        temp_label.pack(side='right')
        
        # Weather condition
        condition_label = tk.Label(weather_info, text=f"☁️ {condition.title()}", 
                                  bg='#f8f9fa', fg='#34495e', 
                                  font=("Segoe UI", 12))
        condition_label.pack(pady=(0, 15))
    
    def display_main_suggestion(self, weather_data):
        """Display main activity suggestion"""
        temp = weather_data['temp']
        condition = weather_data['weather_summary']
        
        # Get suggestion and color
        suggestion = suggest_activity(temp, condition)
        color = get_activity_color(temp, condition)
        
        # Main suggestion container
        suggestion_container = tk.Frame(self.main_suggestion_frame, bg=color, relief='flat', bd=1)
        suggestion_container.pack(fill='x', pady=10)
        
        # Suggestion text
        suggestion_text = tk.Label(suggestion_container, text=suggestion, 
                                  bg=color, fg='#ffffff', 
                                  font=("Segoe UI", 14, "bold"),
                                  wraplength=600,
                                  justify="center")
        suggestion_text.pack(pady=20)
    
    def display_alternative_activities(self, weather_data):
        """Display alternative activity options"""
        temp_f = (weather_data['temp'] * 9/5) + 32
        condition = weather_data['weather_summary'].lower()
        
        # Determine activity categories
        activities = self.get_activity_suggestions(temp_f, condition)
        
        # Create activity grid
        activity_grid = tk.Frame(self.options_display, bg='#ffffff')
        activity_grid.pack(fill='x', pady=10)
        
        # Display activities in rows
        for i, (category, activity_list) in enumerate(activities.items()):
            # Category frame
            category_frame = tk.Frame(activity_grid, bg='#ffffff')
            category_frame.pack(fill='x', pady=5)
            
            # Category title
            category_title = tk.Label(category_frame, text=category, 
                                     bg='#ffffff', fg='#2c3e50', 
                                     font=("Segoe UI", 12, "bold"))
            category_title.pack(anchor='w', pady=(5, 0))
            
            # Activity buttons
            buttons_frame = tk.Frame(category_frame, bg='#ffffff')
            buttons_frame.pack(fill='x', pady=(5, 0))
            
            for j, activity in enumerate(activity_list):
                btn = tk.Button(buttons_frame, text=activity, 
                               bg='#ecf0f1', fg='#2c3e50', 
                               font=("Segoe UI", 10), 
                               relief='flat', bd=1, padx=15, pady=8,
                               cursor='hand2',
                               command=lambda a=activity: self.show_activity_detail(a))
                btn.pack(side='left', padx=(0, 10))
    
    def get_activity_suggestions(self, temp_f, condition):
        """Get categorized activity suggestions"""
        activities = {}
        
        # Indoor activities
        if temp_f < 40 or "rain" in condition or "snow" in condition:
            activities["🏠 Indoor Activities"] = [
                "🏋️ Home Workout", "☕ Coffee Shop Visit", "🎮 Gaming Session",
                "📚 Reading Time", "🍳 Cooking Project"
            ]
        
        # Outdoor activities
        if temp_f > 50 and "rain" not in condition:
            activities["🌳 Outdoor Activities"] = [
                "🚶 Nature Walk", "🚴 Bike Ride", "🏃 Jogging",
                "📸 Photography", "🌳 Park Visit"
            ]
        
        # Seasonal activities
        if temp_f > 75:
            activities["☀️ Summer Activities"] = [
                "🏊 Swimming", "🏖️ Beach Day", "🍦 Ice Cream Run",
                "💧 Water Sports", "🌅 Sunrise/Sunset"
            ]
        elif temp_f < 50:
            activities["❄️ Cool Weather"] = [
                "🛍️ Shopping", "🏛️ Museum Visit", "🎬 Movie Theater",
                "🧣 Cozy Activities", "🔥 Fireplace Time"
            ]
        
        return activities
    
    def show_activity_detail(self, activity):
        """Show detailed information about an activity"""
        messagebox.showinfo("Activity Suggestion", 
                          f"Great choice! {activity} is perfect for today's weather conditions.\n\n"
                          f"Enjoy your activity and stay safe!")

# import tkinter as tk
# from tkinter import ttk
# from tkinter import ttk, messagebox
# def suggest_activity(temp, condition):
#     """
#     Enhanced activity suggestions based on temperature and weather conditions
    
#     Args:
#         temp (float): Temperature in Celsius
#         condition (str): Weather condition description
        
#     Returns:
#         str: Activity suggestion with appropriate emoji
#     """
#     condition_lower = condition.lower()
#     temp_f = (temp * 9/5) + 32  # Convert to Fahrenheit for easier reading
    
#     # Weather-based suggestions
#     if any(word in condition_lower for word in ["rain", "drizzle", "shower"]):
#         return "☔ Perfect for indoor activities - read a book, cook, or watch movies!"
#     elif any(word in condition_lower for word in ["snow", "blizzard", "ice"]):
#         return "❄️ Winter wonderland! Build a snowman or enjoy hot cocoa inside!"
#     elif any(word in condition_lower for word in ["storm", "thunder", "lightning"]):
#         return "⚡ Stay safe indoors - great time for board games or creative projects!"
#     elif any(word in condition_lower for word in ["fog", "mist", "haze"]):
#         return "🌫️ Limited visibility - perfect for indoor workout or meditation!"
    
#     # Temperature-based suggestions
#     if temp_f < 32:  # Below freezing
#         return "🧊 Bundle up! Perfect for winter sports or cozy indoor activities!"
#     elif temp_f < 50:  # Cold
#         return "🧥 Chilly day - great for brisk walks, shopping, or museum visits!"
#     elif temp_f < 70:  # Cool/Mild
#         return "🍂 Perfect weather for hiking, cycling, or outdoor photography!"
#     elif temp_f < 80:  # Comfortable
#         return "🌞 Beautiful day! Ideal for picnics, gardening, or outdoor sports!"
#     elif temp_f < 90:  # Warm
#         return "🏖️ Great beach weather! Swimming, barbecue, or park activities!"
#     else:  # Hot
#         return "🌡️ Stay cool! Early morning walks, indoor activities, or pool time!"

# def get_activity_color(temp, condition):
#     """
#     Get appropriate color for activity suggestion based on conditions
    
#     Args:
#         temp (float): Temperature in Celsius
#         condition (str): Weather condition
        
#     Returns:
#         str: Hex color code
#     """
#     condition_lower = condition.lower()
    
#     if any(word in condition_lower for word in ["rain", "storm", "snow"]):
#         return "#64748b"  # Gray for weather warnings
#     elif temp < 0:
#         return "#3b82f6"  # Blue for cold
#     elif temp < 20:
#         return "#10b981"  # Green for mild
#     elif temp < 30:
#         return "#f59e0b"  # Yellow for warm
#     else:
#         return "#ef4444"  # Red for hot

# class ActivityPanel:
#     """Enhanced activity panel with better styling and more features"""
    
#     def __init__(self, parent_tab, fetcher, db):
#         self.fetcher = fetcher
#         self.db = db
        
#         # Main frame with modern styling
#         self.frame = ttk.Frame(parent_tab, style="Modern.TFrame")
#         self.frame.pack(expand=True, fill='both', padx=20, pady=20)
        
#         # Header
#         header_frame = ttk.Frame(self.frame, style="Modern.TFrame")
#         header_frame.pack(fill='x', pady=(0, 20))
        
#         ttk.Label(header_frame, text="🎯 Activity Suggestions", 
#                  style="Title.TLabel").pack(side='left')
        
#         # Location selector
#         location_frame = ttk.LabelFrame(self.frame, text="📍 Select Location", 
#                                        style="Card.TLabelframe")
#         location_frame.pack(fill='x', pady=(0, 20))
        
#         location_controls = ttk.Frame(location_frame, style="Modern.TFrame")
#         location_controls.pack(pady=10)
        
#         ttk.Label(location_controls, text="City:", style="Modern.TLabel").grid(row=0, column=0, padx=5)
#         self.city_entry = ttk.Entry(location_controls, width=20, style="Modern.TEntry")
#         self.city_entry.grid(row=0, column=1, padx=5)
#         self.city_entry.insert(0, "Knoxville")
        
#         ttk.Label(location_controls, text="Country:", style="Modern.TLabel").grid(row=0, column=2, padx=5)
#         self.country_entry = ttk.Entry(location_controls, width=5, style="Modern.TEntry")
#         self.country_entry.grid(row=0, column=3, padx=5)
#         self.country_entry.insert(0, "US")
        
#         ttk.Button(location_controls, text="🔍 Get Suggestions", 
#                   style="Modern.TButton", command=self.update_suggestions).grid(row=0, column=4, padx=10)
        
#         # Activity display area
#         self.activity_frame = ttk.LabelFrame(self.frame, text="Today's Activity Suggestions", 
#                                            style="Card.TLabelframe")
#         self.activity_frame.pack(fill='both', expand=True, pady=(0, 20))
        
#         # Current conditions display
#         self.conditions_frame = ttk.Frame(self.activity_frame, style="Modern.TFrame")
#         self.conditions_frame.pack(fill='x', pady=10)
        
#         # Activity suggestion display
#         self.suggestion_label = ttk.Label(self.activity_frame, 
#                                         text="Click 'Get Suggestions' to see activity recommendations",
#                                         style="Modern.TLabel", 
#                                         wraplength=400,
#                                         justify="center")
#         self.suggestion_label.pack(pady=20)
        
#         # Multiple activity options
#         self.options_frame = ttk.LabelFrame(self.frame, text="Alternative Activities", 
#                                           style="Card.TLabelframe")
#         self.options_frame.pack(fill='x')
        
#         # Auto-load suggestions for default city
#         self.frame.after(100, self.update_suggestions)
    
#     def update_suggestions(self):
#         """Update activity suggestions based on current weather"""
#         city = self.city_entry.get().strip() or "Knoxville"
#         country = self.country_entry.get().strip() or "US"
        
#         # Clear previous suggestions
#         for widget in self.conditions_frame.winfo_children():
#             widget.destroy()
#         for widget in self.options_frame.winfo_children():
#             widget.destroy()
        
#         # Fetch current weather
#         weather_data = self.fetcher.fetch_current_weather(city, country)
        
#         if weather_data:
#             # Display current conditions
#             temp_f = (weather_data['temp'] * 9/5) + 32
#             condition = weather_data['weather_summary']
            
#             # Weather info display
#             weather_info = ttk.Frame(self.conditions_frame, style="Modern.TFrame")
#             weather_info.pack(fill='x', pady=5)
            
#             ttk.Label(weather_info, text=f"📍 {city}, {country}", 
#                      style="Modern.TLabel", font=("Segoe UI", 12, "bold")).pack(side='left')
            
#             ttk.Label(weather_info, text=f"🌡️ {temp_f:.1f}°F", 
#                      style="Modern.TLabel", font=("Segoe UI", 12)).pack(side='right')
            
#             ttk.Label(weather_info, text=f"☁️ {condition.title()}", 
#                      style="Modern.TLabel", font=("Segoe UI", 12)).pack(side='right', padx=10)
            
#             # Main activity suggestion
#             main_suggestion = suggest_activity(weather_data['temp'], condition)
#             self.suggestion_label.config(text=main_suggestion)
            
#             # Additional activity options
#             self.show_activity_options(weather_data['temp'], condition)
            
#         else:
#             self.suggestion_label.config(text="❌ Could not fetch weather data for activity suggestions")
    
#     def update_activity_suggestions(self, weather_data):
#         """Update activity suggestions based on weather data"""
#         suggestion = suggest_activity(weather_data['temp'], weather_data['weather_summary'])
#         activity_color = get_activity_color(weather_data['temp'], weather_data['weather_summary'])
        
#         # Clear previous suggestions
#         for widget in self.activity_frame.winfo_children():
#             widget.destroy()
        
#         # Create activity suggestion display
#         activity_content = ttk.Frame(self.activity_frame, style="Card.TFrame")
#         activity_content.pack(fill='both', expand=True, padx=15, pady=15)
        
#         # Current conditions
#         conditions_frame = ttk.Frame(activity_content, style="Card.TFrame")
#         conditions_frame.pack(fill='x', pady=(0, 15))
        
#         temp_f = (weather_data['temp'] * 9/5) + 32
#         condition_summary = ttk.Label(conditions_frame, 
#                                     text=f"🌡️ {temp_f:.1f}°F | {weather_data['weather_summary'].title()}",
#                                     style="Card.TLabel",
#                                     font=("Segoe UI", 12))
#         condition_summary.pack()
        
#         # Main suggestion
#         suggestion_label = ttk.Label(activity_content, 
#                                    text=suggestion,
#                                    style="Card.TLabel",
#                                    font=("Segoe UI", 14, "bold"),
#                                    wraplength=220,
#                                    justify="center")
#         suggestion_label.pack(pady=10)
        
#         # Additional suggestions based on weather
#         # self.add_activity_suggestions(activity_content, weather_data)
#         self.show_activity_options(activity_content, weather_data)
#     def show_activity_options(self, parent, weather_data):
#         """Add additional activity suggestions"""
#         temp_f = (weather_data['temp'] * 9/5) + 32
#         condition = weather_data['weather_summary'].lower()
        
#         suggestions = []
        
#         if temp_f < 40:
#             suggestions.extend(["🏠 Indoor workout", "☕ Cozy cafe visit", "🎮 Gaming session"])
#         elif temp_f < 70:
#             suggestions.extend(["🚶 Nature walk", "📚 Outdoor reading", "🛍️ Shopping trip"])
#         elif temp_f < 85:
#             suggestions.extend(["🏊 Swimming", "🌳 Park picnic", "🚴 Bike ride"])
#         else:
#             suggestions.extend(["🏢 Mall visit", "🍦 Ice cream run", "💧 Water activities"])
        
#         if "rain" in condition:
#             suggestions = ["☔ Museum visit", "🎬 Movie theater", "🍳 Cooking class"]
#         elif "snow" in condition:
#             suggestions = ["⛄ Snow activities", "🔥 Fireplace time", "🧣 Winter sports"]
        
#         # Display suggestions
#         for suggestion in suggestions[:3]:  # Limit to 3 suggestions
#             suggestion_btn = ttk.Button(parent, text=suggestion, 
#                                       style="Modern.TButton",
#                                       command=lambda s=suggestion: self.show_activity_detail(s))
#             suggestion_btn.pack(fill='x', pady=2)
    
#     def show_activity_detail(self, activity):
#         """Show detailed information about an activity"""
#         messagebox.showinfo("Activity Detail", f"Great choice! {activity} is perfect for today's weather.")
    