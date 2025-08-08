from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import pandas as pd
from services.weather_stats import get_weather_stats
from features.theme_switcher import ThemeManager
from components.creater_header import CreateHeader
from components.create_feature_tabs import CreateFeatureTabs
from components.display_features_ui import DisplayFeatures
from components.get_weather import GetWeather
from components.create_dashboard_layout_ui import CreateDashboardLayout
from config import Config
from dotenv import load_dotenv
from features.emoji import WeatherEmoji

load_dotenv()
cfg = Config.load_from_env()

class WeatherAppGUI:
    def __init__(self, fetcher, db, tracker, logger, cfg):
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger
        self.cfg = cfg
        self.current_weather_data = None

        # UI references
        self.temp_label = None
        self.city_label = None
        self.desc_label = None
        self.icon_label = None
        self.details_frame = None
        self.forecast_items_frame = None
        self.graph_container = None
        self.activity_content_frame = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("🌤️ Weather Dashboard Pro")
        self.root.geometry("2000x1200")
        self.root.configure(bg="#f8fafc")

        # Configure main grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Initialize theme manager (but don't use toggle functionality)
        self.theme_manager = ThemeManager(self.root)
        self.weather_graphs = None

        self.setup_components()

        # Start weather fetch after UI initializes
        self.root.after(1000, self.start_default_weather_fetch)

        # Summary label
        self.summary_label = ttk.Label(self.root, text="", font=("Segoe UI", 10), foreground="#334155")
        self.summary_label.grid(row=2, column=0, sticky="w", padx=20, pady=(10, 0))

    def setup_components(self):
        
        # 1. Create GetWeather component first
        self.get_weather_component = GetWeather(
            fetcher=self.fetcher,
            db=self.db,
            logger=self.logger,
            root=self.root
        )
        self.get_weather = self.get_weather_component

        # 2. Feature Tabs Component - Create this NEXT
        self.feature_tabs_component = CreateFeatureTabs(
            parent=self.root,
            fetcher=self.fetcher,
            db=self.db,
            tracker=self.tracker,
            logger=self.logger,
            theme_manager=self.theme_manager,
            cfg=self.cfg,
            get_city_callback=self.get_city,
            export_data_callback=self.export_data
        )
        
        # Create the notebook from tabs component
        self.notebook = self.feature_tabs_component.create_tab_interface()

        # 3. Dashboard Layout Component - Add dashboard to existing notebook
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.insert(0, dashboard_frame, text="🌤️ Dashboard")
        
        # Create dashboard layout component
        self.dashboard_layout_component = CreateDashboardLayout(
            parent=dashboard_frame,
            theme_manager=self.theme_manager,
            db=self.db,
            logger=self.logger,
            fetcher=self.fetcher,
            cfg=self.cfg
        )
        
        # Create dashboard layout FIRST
        self.dashboard_layout_component.create_dashboard_layout()
        
        # THEN collect widget references
        self.collect_widget_references()

        # 4. Display Features Component
        self.display_features_component = DisplayFeatures(
            parent=self.root,
            theme_manager=self.theme_manager,
            db=self.db,
            logger=self.logger,
            fetcher=self.fetcher,
            cfg=self.cfg,
            city_entry=None, 
            country_entry=None  
        )
        
        # 5. Set up refresh callbacks BEFORE creating header
        refresh_callbacks = {
            'weather_data': self.get_weather_component.get_weather_threaded,
            'dashboard_hourly': lambda city, country: self.dashboard_layout_component.update_hourly_forecast(
                city, country, "imperial" if country.upper() == "US" else "metric"
            ) if hasattr(self.dashboard_layout_component, 'update_hourly_forecast') else None,
            'temperature_graph': lambda city, country: self.display_features_component.update_temperature_graph(city, country),
            'tomorrow_prediction': lambda city, country: self.feature_tabs_component.update_tomorrow_prediction_location(city, country),
            'forecast_display': lambda city, country: self.display_features_component.refresh_for_location(city, country),
            'all_panels_update': lambda city, country: self.feature_tabs_component.update_location_for_all_panels(city, country),
            'refresh_all_panels': lambda city, country: self.feature_tabs_component.refresh_all_panels()
        }
        
        # 6. Create Header Component with proper callbacks
        self.header_component = CreateHeader(
            root=self.root,
            get_weather_callback=self.get_weather_component.get_weather_threaded,
            refresh_callbacks=refresh_callbacks
        )

        # 7. Get entry references from header
        self.city_entry = self.header_component.city_entry
        self.country_entry = self.header_component.country_entry
        
        # 8. Set ALL UI references for GetWeather component
        self.get_weather_component.set_ui_references(
            city_entry=self.city_entry,
            country_entry=self.country_entry,
            temp_label=self.temp_label,
            city_label=self.city_label,
            desc_label=self.desc_label,
            icon_label=self.icon_label,
            details_frame=self.details_frame,
            forecast_items_frame=self.forecast_items_frame,
            hourly_scroll_frame=getattr(self, 'hourly_scroll_frame', None),
            graph_container=self.graph_container
        )
        
        # 9. Set display component reference
        self.get_weather_component.set_display_component(self.display_features_component)
        
        # 10. Set UI references for display component
        self.display_features_component.set_ui_references(
            temp_label=self.temp_label,
            city_label=self.city_label,
            desc_label=self.desc_label,
            icon_label=self.icon_label,
            details_frame=self.details_frame,
            forecast_items_frame=self.forecast_items_frame,
            hourly_scroll_frame=getattr(self, 'hourly_scroll_frame', None),
            graph_container=self.graph_container,
            activity_content_frame=self.activity_content_frame
        )
        
        # Update display component with entry references
        self.display_features_component.city_entry = self.city_entry
        self.display_features_component.country_entry = self.country_entry

        # 11. Register callbacks - This is CRITICAL!
        self.get_weather_component.register_callback('on_weather_success', 
            self.display_features_component.display_current_weather)
        self.get_weather_component.register_callback('on_forecast_success', 
            self.display_features_component.display_forecast)
        
        # 12. Register weather display callback for dashboard
        self.get_weather_component.register_callback(
            "on_weather_success", 
            self.dashboard_layout_component.update_weather_display
        )
        self.get_weather_component.register_callback(
            'on_weather_success',
            lambda weather_data, units: self.feature_tabs_component.update_weather_data(weather_data)
        )
        self.get_weather_component.register_callback(
            'on_weather_success',
            lambda weather_data, units: self.feature_tabs_component.update_tomorrow_prediction_location(
                weather_data.get('city', self.get_city()),
                self.country_entry.get().strip() or "US"
            )
        )
        
        # 13. Optional: Register temperature graph callback if it exists
        if hasattr(self.display_features_component, 'update_temperature_graph'):
            self.get_weather_component.register_callback(
                'on_weather_success',
                lambda weather_data, units: self.display_features_component.update_temperature_graph(
                    self.get_city(),
                    self.country_entry.get().strip() or "US"
                )
            )
            
        # 14. Set UI references for dashboard component
        if hasattr(self.dashboard_layout_component, 'set_ui_references'):
            self.dashboard_layout_component.set_ui_references(
                city_entry=self.city_entry,
                country_entry=self.country_entry
            )

        # 15. Register location change callback - MOVED INSIDE METHOD
        self.get_weather_component.register_callback('on_weather_success', self.on_location_change_callback)

        print("DEBUG: Setup components completed with all refresh callbacks configured")
        print(f"DEBUG: Refresh callbacks registered: {list(refresh_callbacks.keys())}")
        
        # Log the callback registrations for debugging
        for callback_type, callbacks in self.get_weather_component.ui_callbacks.items():
            print(f"DEBUG: {callback_type}: {len(callbacks)} callbacks registered")

    def on_location_change_callback(self, weather_data, units):
        """Called when weather data changes - updates all location-dependent features"""
        try:
            city = weather_data.get('city', self.get_city())
            country = self.country_entry.get().strip() or "US"
            
            # Update all panels with new location
            self.feature_tabs_component.update_location_for_all_panels(city, country)
            
            # Specifically update tomorrow's prediction
            self.feature_tabs_component.update_tomorrow_prediction_location(city, country)
            
            self.logger.info(f"Location change processed for {city}, {country}")
            
        except Exception as e:
            self.logger.error(f"Error in location change callback: {e}")

    def start_default_weather_fetch(self):
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, "Knoxville")
        self.country_entry.delete(0, tk.END)
        self.country_entry.insert(0, "US")
        
        # Now fetch weather using the entries
        self.get_weather_component.get_weather_threaded()

    def collect_widget_references(self):
        """Collect widget references from dashboard layout component"""
        if hasattr(self.dashboard_layout_component, 'widgets'):
            widgets = self.dashboard_layout_component.widgets
            self.temp_label = widgets.get('temp_label')
            self.city_label = widgets.get('city_label')
            self.desc_label = widgets.get('desc_label')
            self.icon_label = widgets.get('icon_label')
            self.details_frame = widgets.get('details_frame')
            self.forecast_items_frame = widgets.get('forecast_items_frame')
            self.graph_container = widgets.get('graph_container')
            self.hourly_scroll_frame = widgets.get('hourly_scroll_frame')
            
            # Log what we found
            self.logger.info(f"Collected widget references:")
            for name, widget in widgets.items():
                self.logger.info(f"  {name}: {'Found' if widget else 'None'}")
        else:
            self.logger.error("Dashboard layout component has no widgets attribute")

    def get_weather_threaded(self):
        """Use component's weather fetching"""
        self.get_weather_component.get_weather_threaded()

    def get_city(self):
        return self.city_entry.get().strip() or "Knoxville"

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
                    messagebox.showinfo("Export Successful", f"Weather data exported to:\n{filename}")
                else:
                    messagebox.showwarning("Export Failed", "No weather records available to export.")
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.logger.info("Weather Dashboard application closing")
