import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from .activity_suggester import ActivitySuggester

class ActivityPanel:
    def __init__(self, parent_tab, fetcher, db, logger, tracker, cfg):
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger
     
        self.configure_styles()
        self.current_weather_data = None


        self.main_container = tk.Frame(parent_tab, bg='#f0f2f5')
        self.main_container.pack(expand=True, fill='both')
        

        self.scrollable_frame = tk.Frame(self.main_container, bg='#f0f2f5')
        self.scrollable_frame.pack(fill="both", expand=True)
        
        self.create_header()
        self.create_weather_section()
        self.create_activity_section()
        self.create_options_section()
        
        self.main_container.after(100, self.update_suggestions)
    
    def configure_styles(self):
        style = ttk.Style()        

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
        
        style.configure("Modern.TButton", font=("Segoe UI", 10), padding=10)
        style.configure("Activity.TButton", font=("Segoe UI", 10), padding=8)
        
        style.configure("Modern.TEntry", font=("Segoe UI", 10), padding=5)
        
        style.configure("Card.TLabelframe", background="#ffffff", foreground="#2c3e50",
                       font=("Segoe UI", 11, "bold"))
        style.configure("Card.TLabelframe.Label", background="#ffffff", foreground="#2c3e50",
                       font=("Segoe UI", 11, "bold"))
    
    def create_scrollable_frame(self):      
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_container, bg='#f0f2f5', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#f0f2f5')        
    
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)        

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):      
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_header(self):
        header_frame = tk.Frame(self.scrollable_frame, bg='#2c3e50', height=80)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#2c3e50')
        header_content.pack(expand=True, fill='both', padx=30, pady=20)
    
        title_label = tk.Label(header_content, text="🎯 Activity Suggestions", 
                              bg='#2c3e50', fg='#ffffff', 
                              font=("Segoe UI", 20, "bold"))
        title_label.pack(side='left', anchor='w')
        subtitle_label = tk.Label(header_content, text="Find the perfect activity for today's weather", 
                                 bg='#2c3e50', fg='#bdc3c7', 
                                 font=("Segoe UI", 12))
        subtitle_label.pack(side='left', anchor='w', padx=(20, 0))
    
    def create_weather_section(self):
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

        city_frame = tk.Frame(location_frame, bg='#ffffff')
        city_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(city_frame, text="City:", bg='#ffffff', fg='#2c3e50', 
                font=("Segoe UI", 10)).pack(anchor='w')
        self.city_entry = tk.Entry(city_frame, font=("Segoe UI", 10), width=15, 
                                  relief='flat', bd=1, bg='#f8f9fa')
        self.city_entry.pack(pady=(5, 0))
        self.city_entry.insert(0, "Knoxville")

        country_frame = tk.Frame(location_frame, bg='#ffffff')
        country_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(country_frame, text="Country:", bg='#ffffff', fg='#2c3e50', 
                font=("Segoe UI", 10)).pack(anchor='w')
        self.country_entry = tk.Entry(country_frame, font=("Segoe UI", 10), width=8, 
                                     relief='flat', bd=1, bg='#f8f9fa')
        self.country_entry.pack(pady=(5, 0))
        self.country_entry.insert(0, "US")
        
      
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
        
        self.options_display = tk.Frame(options_frame, bg='#ffffff')
        self.options_display.pack(fill='x', padx=20, pady=(0, 20))
    
    def update_suggestions(self):      
        city = self.city_entry.get().strip() or "Knoxville"
        country = self.country_entry.get().strip() or "US"
        
       
        for widget in self.weather_display.winfo_children():
            widget.destroy()
        for widget in self.main_suggestion_frame.winfo_children():
            widget.destroy()
        for widget in self.options_display.winfo_children():
            widget.destroy()
        
        loading_label = tk.Label(self.weather_display, text="🔄 Loading weather data...", 
                               bg='#ffffff', fg='#7f8c8d', 
                               font=("Segoe UI", 11))
        loading_label.pack(pady=10)
        self.scrollable_frame.update()
        
        # Fetch current weather
        try:
            weather_data = self.fetcher.fetch_current_weather(city, country)
            
            if weather_data:
                # Clear loading message
                loading_label.destroy()
                                
                self.display_weather_info(weather_data, city, country)
                self.display_main_suggestion(weather_data)                
                self.display_alternative_activities(weather_data)
                self.current_weather_data = weather_data
            else:
                loading_label.config(text="❌ Could not fetch weather data. Please check your connection.")
                
        except Exception as e:
            loading_label.config(text=f"❌ Error: {str(e)}")
    
    def display_weather_info(self, weather_data, city, country):
        temp_f = weather_data.get("temp")  
        condition = weather_data['weather_summary']
        
        # Weather info container
        weather_info = tk.Frame(self.weather_display, bg='#f8f9fa', relief='flat', bd=1)
        weather_info.pack(fill='x', pady=10)
        
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
        temp = weather_data['temp']
        condition = weather_data['weather_summary']
        
        suggester = ActivitySuggester(temp, condition)
        suggestion = suggester.get_suggestion()
        color = suggester.get_color()     
        suggestion_container = tk.Frame(self.main_suggestion_frame, bg=color, relief='flat', bd=1)
        suggestion_container.pack(fill='x', pady=10)
        suggestion_text = tk.Label(suggestion_container, text=suggestion, 
                                  bg=color, fg='#ffffff', 
                                  font=("Segoe UI", 14, "bold"),
                                  wraplength=600,
                                  justify="center")
        suggestion_text.pack(pady=20)
    
    def display_alternative_activities(self, weather_data):      
        temp_f = weather_data.get("temp")
        if not isinstance(temp_f, (int, float)):
            temp_f = "--"


        condition = weather_data['weather_summary'].lower()        
       
        activities = self.get_activity_suggestions(temp_f, condition)
        # Create activity grid
        activity_grid = tk.Frame(self.options_display, bg='#ffffff')
        activity_grid.pack(fill='x', pady=10)
        
        # Display activities in rows
        for i, (category, activity_list) in enumerate(activities.items()):
            category_frame = tk.Frame(activity_grid, bg='#ffffff')
            category_frame.pack(fill='x', pady=5)
            category_title = tk.Label(category_frame, text=category, 
                                     bg='#ffffff', fg='#2c3e50', 
                                     font=("Segoe UI", 12, "bold"))
            category_title.pack(anchor='w', pady=(5, 0))            

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
        activities = {}
        
        if temp_f < 40 or "rain" in condition or "snow" in condition:
            activities["🏠 Indoor Activities"] = [
                "🏋️ Home Workout", "☕ Coffee Shop Visit", "🎮 Gaming Session",
                "📚 Reading Time", "🍳 Cooking Project"
            ]
        
        if temp_f > 50 and "rain" not in condition:
            activities["🌳 Outdoor Activities"] = [
                "🚶 Nature Walk", "🚴 Bike Ride", "🏃 Jogging",
                "📸 Photography", "🌳 Park Visit"
            ]
        
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
        messagebox.showinfo("Activity Suggestion", 
                          f"Great choice! {activity} is perfect for today's weather conditions.\n\n"
                          f"Enjoy your activity and stay safe!")
        
        
    def show_activity_suggestion(self):
        if self.current_weather_data:
            try:
                weather_condition = self.current_weather_data.get('weather_summary', 'Clear')
                suggester = ActivitySuggester(self.current_weather_data['temp'], weather_condition)
                activity = suggester.get_suggestion()
                messagebox.showinfo("Activity Suggestion", 
                                f"Based on current weather in {self.current_weather_data['city']}:\n\n"
                                f"🎯 Suggested Activity: {activity}")
            except Exception as e:
                self.logger.error(f"Error getting activity suggestion: {e}")
                messagebox.showinfo("Activity Suggestion", "Unable to get activity suggestion at this time.")
        else:
            messagebox.showinfo("Activity Suggestion", "Please search for weather first!")
