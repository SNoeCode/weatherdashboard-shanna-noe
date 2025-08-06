import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class ActivitySuggester:
    def __init__(self, temp_c: float, condition: str):
        self.temp_c = temp_c
        self.condition = condition.lower()
        self.temp_f = temp_c
        self.current_weather_data = None

    def get_suggestion(self) -> str:
        if any(word in self.condition for word in ['rain', 'drizzle', 'shower']):
            return "☔ Perfect for indoor activities - read a book, cook, or watch movies!"
        elif any(word in self.condition for word in ['snow', 'blizzard', 'ice']):
            return "❄️ Winter wonderland! Build a snowman or enjoy hot cocoa inside!"
        elif any(word in self.condition for word in ['storm', 'thunder', 'lightning']):
            return "⚡ Stay safe indoors - great time for board games or creative projects!"
        elif any(word in self.condition for word in ['fog', 'mist', 'haze']):
            return "🌫️ Limited visibility - perfect for indoor workout or meditation!"
                
        if self.temp_f < 32:
            return "🧊 Bundle up! Perfect for winter sports or cozy indoor activities!"
        elif self.temp_f < 50:
            return "🧥 Chilly day - great for brisk walks, shopping, or museum visits!"
        elif self.temp_f < 70:
            return "🍂 Perfect weather for hiking, cycling, or outdoor photography!"
        elif self.temp_f < 80:
            return "🌞 Beautiful day! Ideal for picnics, gardening, or outdoor sports!"
        elif self.temp_f < 90:
            return "🏖️ Great beach weather! Swimming, barbecue, or park activities!"
        else:
            return "🌡️ Stay cool! Early morning walks, indoor activities, or pool time!"

    def get_color(self) -> str:
        if any(word in self.condition for word in ['rain', 'storm', 'snow']):
            return "#64748b"
        elif self.temp_c < 0:
            return "#3b82f6"
        elif self.temp_c < 20:
            return "#10b981"
        elif self.temp_c < 30:
            return "#f59e0b"
        else:
            return "#ef4444"

class ActivityPanel:
    def __init__(self, parent_tab, fetcher, db, logger, tracker, cfg):
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger
        self.cfg = cfg
     
        self.current_weather_data = None        

        self.main_container = tk.Frame(parent_tab, bg='#fef7ff')
        self.main_container.pack(expand=True, fill='both', padx=5, pady=5) 
        
        self.create_header()
        self.create_weather_section()
        self.create_activity_section()
        self.create_options_section()
        
        # Auto-update after initialization
        self.main_container.after(100, self.update_suggestions)
    
    def create_header(self):
        """Create COMPACT header with reduced size"""
        header_frame = tk.Frame(self.main_container, bg='#9333ea', height=50)  
        header_frame.pack(fill='x', pady=(0, 10)) 
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#9333ea')
        header_content.pack(expand=True, fill='both', padx=15, pady=8) 
    
        title_label = tk.Label(header_content, text="🎯 Activity Suggestions", 
                              bg='#9333ea', fg='#ffffff', 
                              font=("Segoe UI", 14, "bold"))  
        title_label.pack(anchor='center')
        
        subtitle_label = tk.Label(header_content, text="Quick activity recommendations", 
                                 bg='#9333ea', fg='#e9d5ff', 
                                 font=("Segoe UI", 9)) 
        subtitle_label.pack(anchor='center', pady=(2, 0)) 
    
    def create_weather_section(self):
        """Create COMPACT weather input section"""
        weather_container = tk.Frame(self.main_container, bg='#ffffff', relief='solid', bd=1)
        weather_container.pack(fill='x', padx=10, pady=(0, 10)) 
        
        # Weather section header 
        weather_header = tk.Frame(weather_container, bg='#0ea5e9', height=30) 
        weather_header.pack(fill='x')
        weather_header.pack_propagate(False)
        
        weather_title = tk.Label(weather_header, text="📍 Location & Weather", 
                                bg='#0ea5e9', fg='#ffffff', 
                                font=("Segoe UI", 10, "bold"))  
        weather_title.pack(expand=True)
        
        # COMPACT location input section
        location_frame = tk.Frame(weather_container, bg='#ffffff')
        location_frame.pack(fill='x', padx=15, pady=10) 

        # Compact input fields container
        inputs_container = tk.Frame(location_frame, bg='#ffffff')
        inputs_container.pack(fill='x')

        # City input - SMALLER
        city_frame = tk.Frame(inputs_container, bg='#ffffff')
        city_frame.pack(side='left', padx=(0, 10)) 
        
        tk.Label(city_frame, text="🏙️ City:", bg='#ffffff', fg='#1e293b', 
                font=("Segoe UI", 8, "bold")).pack(anchor='w')  
        self.city_entry = tk.Entry(city_frame, font=("Segoe UI", 9), width=12, 
                                  relief='solid', bd=1, bg='#f8fafc', fg='#1e293b')
        self.city_entry.pack(pady=(2, 0))
        self.city_entry.insert(0, "Knoxville")

        # Country input
        country_frame = tk.Frame(inputs_container, bg='#ffffff')
        country_frame.pack(side='left', padx=(0, 10))
        
        tk.Label(country_frame, text="🌍 Country:", bg='#ffffff', fg='#1e293b', 
                font=("Segoe UI", 8, "bold")).pack(anchor='w') 
        self.country_entry = tk.Entry(country_frame, font=("Segoe UI", 9), width=6, 
                                     relief='solid', bd=1, bg='#f8fafc', fg='#1e293b')
        self.country_entry.pack(pady=(2, 0))
        self.country_entry.insert(0, "US")
        
        # COMPACT update button
        update_btn = tk.Button(inputs_container, text="🔍 Update", 
                              bg='#06b6d4', fg='#ffffff', 
                              font=("Segoe UI", 9, "bold"),  
                              relief='flat', bd=0, padx=15, pady=6,  
                              cursor='hand2',
                              command=self.update_suggestions)
        update_btn.pack(side='left', pady=(15, 0))
        
        # COMPACT weather display area
        self.weather_display = tk.Frame(weather_container, bg='#ffffff')
        self.weather_display.pack(fill='x', padx=15, pady=(0, 15)) 
    
    def create_activity_section(self):     
        activity_container = tk.Frame(self.main_container, bg='#ffffff', relief='solid', bd=1)
        activity_container.pack(fill='x', padx=10, pady=(0, 10))  
        
        # COMPACT activity section header
        activity_header = tk.Frame(activity_container, bg='#dc2626', height=30) 
        activity_header.pack(fill='x')
        activity_header.pack_propagate(False)
        
        activity_title = tk.Label(activity_header, text="🎯 Activity Recommendations", 
                                 bg='#dc2626', fg='#ffffff', 
                                 font=("Segoe UI", 10, "bold"))  
        activity_title.pack(expand=True)
         # COMPACT main suggestion display
        self.main_suggestion_frame = tk.Frame(activity_container, bg='#ffffff')
        self.main_suggestion_frame.pack(fill='x', padx=15, pady=15) 
        
        # Default message 
        default_frame = tk.Frame(self.main_suggestion_frame, bg='#f1f5f9', relief='solid', bd=1)
        default_frame.pack(fill='x', pady=8)  
        
        tk.Label(default_frame, text="🔄", font=("Segoe UI", 20),  
                bg='#f1f5f9').pack(pady=(10, 5))
        self.suggestion_label = tk.Label(default_frame, 
                                        text="Click 'Update' for activity recommendations",
                                        bg='#f1f5f9', fg='#475569', 
                                        font=("Segoe UI", 10), 
                                        wraplength=400,  
                                        justify="center")
        self.suggestion_label.pack(pady=(0, 10))  
    
    def create_options_section(self):    
        options_container = tk.Frame(self.main_container, bg='#ffffff', relief='solid', bd=1)
        options_container.pack(fill='x', padx=10, pady=(0, 10)) 
              
        options_header = tk.Frame(options_container, bg='#f59e0b', height=30)
        options_header.pack(fill='x')
        options_header.pack_propagate(False)
        
        options_title = tk.Label(options_header, text="🎨 Alternative Activities", 
                                bg='#f59e0b', fg='#ffffff', 
                                font=("Segoe UI", 10, "bold"))  
        options_title.pack(expand=True)
        
        self.options_display = tk.Frame(options_container, bg='#ffffff')
        self.options_display.pack(fill='x', padx=15, pady=15) 
        
        # Default message 
        tk.Label(self.options_display, text="🎨 Alternative activities will appear here", 
                font=("Segoe UI", 9), bg='#ffffff', fg='#6b7280').pack(pady=10) 
    
    def update_suggestions(self):             
        city = self.city_entry.get().strip() or "Knoxville"
        country = self.country_entry.get().strip() or "US"
        
        # Clear existing content
        for widget in self.weather_display.winfo_children():
            widget.destroy()
        for widget in self.main_suggestion_frame.winfo_children():
            widget.destroy()
        for widget in self.options_display.winfo_children():
            widget.destroy()
        
        loading_frame = tk.Frame(self.weather_display, bg='#dbeafe', relief='solid', bd=1)
        loading_frame.pack(fill='x', pady=8)  
        
        tk.Label(loading_frame, text="🔄", font=("Segoe UI", 16),  
                bg='#dbeafe').pack(pady=(8, 3))  
        loading_label = tk.Label(loading_frame, text="Loading...", 
                               bg='#dbeafe', fg='#1e40af', 
                               font=("Segoe UI", 9, "bold"))  
        loading_label.pack(pady=(0, 8)) 
        self.main_container.update()
        
        # Fetch current weather
        try:
            weather_data = self.fetcher.fetch_current_weather(city, country)
            if weather_data:
                # Clear loading message
                loading_frame.destroy()
                                
                self.display_weather_info(weather_data, city, country)
                self.display_main_suggestion(weather_data)                
                self.display_alternative_activities(weather_data)
                self.current_weather_data = weather_data
            else:
                loading_label.config(text="❌ Could not fetch weather data",
                                   bg='#fef2f2', fg='#dc2626')
                loading_frame.config(bg='#fef2f2')
                
        except Exception as e:
            loading_label.config(text=f"❌ Error: {str(e)}", bg='#fef2f2', fg='#dc2626')
            loading_frame.config(bg='#fef2f2')
    
    def display_weather_info(self, weather_data, city, country):
        temp_f = weather_data.get("temp")  
        condition = weather_data['weather_summary']
        
        # COMPACT weather info container
        weather_info = tk.Frame(self.weather_display, bg='#f0f9ff', relief='solid', bd=1)
        weather_info.pack(fill='x', pady=8)
        
        # COMPACT weather info header
        info_header = tk.Frame(weather_info, bg='#0284c7', height=25) 
        info_header.pack(fill='x')
        info_header.pack_propagate(False)
        
        tk.Label(info_header, text="📊 Current Weather", 
                font=("Segoe UI", 9, "bold"), bg='#0284c7', fg='#ffffff').pack(expand=True)  
               
        info_content = tk.Frame(weather_info, bg='#f0f9ff')
        info_content.pack(fill='x', padx=12, pady=10)  
        
        # Location and temperature row - COMPACT
        location_temp = tk.Frame(info_content, bg='#f0f9ff')
        location_temp.pack(fill='x', pady=(0, 5))  
        
        location_label = tk.Label(location_temp, text=f"📍 {city}, {country}", 
                                 bg='#f0f9ff', fg='#0c4a6e', 
                                 font=("Segoe UI", 10, "bold"))
        location_label.pack(side='left')
        
        temp_label = tk.Label(location_temp, text=f"🌡️ {temp_f:.1f}°F", 
                             bg='#f0f9ff', fg='#dc2626', 
                             font=("Segoe UI", 10, "bold"))  
        temp_label.pack(side='right')        
       
        condition_frame = tk.Frame(info_content, bg='#e0f2fe', relief='solid', bd=1)
        condition_frame.pack(fill='x', pady=(3, 0))
        
        condition_label = tk.Label(condition_frame, text=f"☁️ {condition.title()}", 
                                  bg='#e0f2fe', fg='#0369a1', 
                                  font=("Segoe UI", 9, "bold")) 
        condition_label.pack(pady=5)
    def display_main_suggestion(self, weather_data):      
        temp = weather_data['temp']
        condition = weather_data['weather_summary']
        
        suggester = ActivitySuggester(temp, condition)
        suggestion = suggester.get_suggestion()
        color = suggester.get_color()
        
        # Create COMPACT suggestion container
        suggestion_container = tk.Frame(self.main_suggestion_frame, bg=color, relief='solid', bd=1)
        suggestion_container.pack(fill='x', pady=8)  
        
    
        icon = "🌞" if temp > 75 else "❄️" if temp < 40 else "🌤️"
        
        tk.Label(suggestion_container, text=icon, font=("Segoe UI", 24), 
                bg=color).pack(pady=(12, 5))  
        
        suggestion_text = tk.Label(suggestion_container, text=suggestion, 
                                  bg=color, fg='#ffffff', 
                                  font=("Segoe UI", 11, "bold"),  
                                  wraplength=400,  
                                  justify="center")
        suggestion_text.pack(pady=(0, 12)) 
    
    def display_alternative_activities(self, weather_data):     
        temp_f = weather_data.get("temp")
        if not isinstance(temp_f, (int, float)):
            temp_f = 70 

        condition = weather_data['weather_summary'].lower()        
       
        activities = self.get_activity_suggestions(temp_f, condition)
        
        if not activities:
            tk.Label(self.options_display, text="🎯 No alternatives available", 
                    font=("Segoe UI", 9), bg='#ffffff', fg='#6b7280').pack(pady=10)  
            return
        
        # Create COMPACT activity grid - limit to 2 categories max
        displayed_count = 0
        for i, (category, activity_list) in enumerate(activities.items()):
            if displayed_count >= 2:  # LIMIT to 2 categories
                break
                
            # Category colors
            category_colors = {
                "🏠 Indoor Activities": ("#fef3c7", "#f59e0b"),
                "🌳 Outdoor Activities": ("#d1fae5", "#10b981"),
                "☀️ Summer Activities": ("#fed7d7", "#ef4444"),
                "❄️ Cool Weather": ("#dbeafe", "#3b82f6")
            }
            
            bg_color, accent_color = category_colors.get(category, ("#f3f4f6", "#6b7280"))
            
            # COMPACT category container
            category_container = tk.Frame(self.options_display, bg=bg_color, relief='solid', bd=1)
            category_container.pack(fill='x', pady=5) 
            
            # COMPACT category header
            category_header = tk.Frame(category_container, bg=accent_color, height=25) 
            category_header.pack(fill='x')
            category_header.pack_propagate(False)
            
            category_title = tk.Label(category_header, text=category, 
                                     bg=accent_color, fg='#ffffff', 
                                     font=("Segoe UI", 9, "bold"))  
            category_title.pack(expand=True)
            
            # COMPACT activity buttons container
            buttons_container = tk.Frame(category_container, bg=bg_color)
            buttons_container.pack(fill='x', padx=8, pady=8) 
            
            buttons_frame = tk.Frame(buttons_container, bg=bg_color)
            buttons_frame.pack()            
        
            for j, activity in enumerate(activity_list[:4]):
                # Create COMPACT activity button
                btn = tk.Button(buttons_frame, text=activity, 
                               bg='#ffffff', fg=accent_color, 
                               font=("Segoe UI", 8, "bold"),  
                               relief='solid', bd=1, padx=8, pady=4, 
                               cursor='hand2',
                               command=lambda a=activity: self.show_activity_detail(a))
                btn.pack(side='left', padx=(0, 5), pady=1) 
                
                # Add hover effects
                def on_enter(e, button=btn, color=accent_color):
                    button.config(bg=color, fg='#ffffff')
                def on_leave(e, button=btn, color=accent_color):
                    button.config(bg='#ffffff', fg=color)
                
                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
            
            displayed_count += 1
    
    def get_activity_suggestions(self, temp_f, condition):       
        activities = {}        
        
        if temp_f < 40 or "rain" in condition or "snow" in condition or temp_f > 95:
            activities["🏠 Indoor Activities"] = [
                "🏋️ Home Workout", "☕ Coffee Shop", "🎮 Gaming",
                "📚 Reading", "🍳 Cooking", "🎨 Art & Crafts"
            ]        
   
        if 50 < temp_f < 90 and "rain" not in condition and "storm" not in condition:
            activities["🌳 Outdoor Activities"] = [
                "🚶 Nature Walk", "🚴 Bike Ride", "🏃 Jogging",
                "📸 Photography", "🌳 Park Visit", "🧺 Picnic"
            ]
               
        if temp_f > 75 and "rain" not in condition:
            activities["☀️ Summer Activities"] = [
                "🏊 Swimming", "🏖️ Beach Day", "🍦 Ice Cream",
                "💧 Water Sports", "🌅 Sunrise Watch", "🏕️ BBQ"
            ]
        
        elif temp_f < 60:
            activities["❄️ Cool Weather"] = [
                "🛍️ Shopping", "🏛️ Museum", "🎬 Movies",
                "🧣 Cozy Time", "🔥 Fireplace", "🍲 Soup Making"
            ]
        
        return activities
    
    def show_activity_detail(self, activity):
        weather_advice = ""
        if self.current_weather_data:
            temp = self.current_weather_data.get('temp', 70)
            condition = self.current_weather_data.get('weather_summary', 'clear')
            
            if temp < 40:
                weather_advice = "\n🧥 Dress warmly!"
            elif temp > 85:
                weather_advice = "\n☀️ Stay hydrated!"
            elif "rain" in condition.lower():
                weather_advice = "\n☔ Bring umbrella!"
        
        messagebox.showinfo("🎯 Activity", 
                          f"{activity} is perfect for today!{weather_advice}")
        
    def show_activity_suggestion(self):     
        if self.current_weather_data:
            try:
                weather_condition = self.current_weather_data.get('weather_summary', 'Clear')
                suggester = ActivitySuggester(self.current_weather_data['temp'], weather_condition)
                activity = suggester.get_suggestion()
                
                messagebox.showinfo("🎯 Activity Suggestion", 
                                f"Based on {weather_condition}, {self.current_weather_data['temp']:.1f}°F:\n\n{activity}")
            except Exception as e:
                self.logger.error(f"Error getting activity suggestion: {e}")
                messagebox.showinfo("🎯 Activity", "Unable to get suggestion. Try updating weather first!")
        else:
            messagebox.showinfo("🎯 Activity", "Please update weather first!")