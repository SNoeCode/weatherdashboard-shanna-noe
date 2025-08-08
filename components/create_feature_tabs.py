import tkinter as tk
from tkinter import ttk
from typing import Optional, Any
from features.activity.activity_panel import ActivityPanel
from features.simple_statistics import SimpleStatsPanel
from features.city_comparisons import CityComparisonPanel
from features.favorites_manager import FavoriteCityPanel
from features.tomorrows_guess import TomorrowGuessPanel
from features.weather_journal import JournalPanel
from features.trends import TrendPanel
from features.graphs_and_charts import GraphsAndChartsPanel
from services.weather_stats import get_weather_stats
from features.insights import InsightsDashboardTab



class CreateFeatureTabs:
    def __init__(self, parent, fetcher, db, tracker, logger, theme_manager, cfg, get_city_callback, export_data_callback):
        self.parent = parent
        self.fetcher = fetcher
        self.db = db
        self.tracker = tracker
        self.logger = logger
        self.theme_manager = theme_manager
        self.cfg = cfg
        self.get_city_callback = get_city_callback
        self.export_data_callback = export_data_callback

        self.graphs_panel: Optional[Any] = None
        self.compare_panel: Optional[Any] = None
        self.insights_panel: Optional[Any] = None   
        self.guess_panel: Optional[Any] = None
        self.stats_display: Optional[tk.Frame] = None
        self.stats_label: Optional[tk.Label] = None
        
        self.notebook: Optional[ttk.Notebook] = None

    def create_tab_interface(self):
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10])  # Wider tabs
        
        self.notebook = ttk.Notebook(self.parent)  # Fixed: use self.parent instead of self.root
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
                
        self.create_graphs_tab()        
        self.create_compare_tab()       
        self.create_insights_tab() 

        return self.notebook

    def create_graphs_tab(self) -> None:        
        if not self.notebook:
            return
            
        graphs_frame = ttk.Frame(self.notebook)
        self.notebook.add(graphs_frame, text="📊 Charts & Graphs")
        
        try:
            self.graphs_panel = GraphsAndChartsPanel(graphs_frame, self.db, self.logger, self.theme_manager)
        except Exception as e:
            self.logger.error(f"Error initializing graphs panel: {e}")
            self._add_error_label(graphs_frame, "📊 Charts & Graphs\n\nGraphs panel will load here")

    def create_compare_tab(self):        
        if not self.notebook:
            return
            
        compare_frame = ttk.Frame(self.notebook)
        self.notebook.add(compare_frame, text="🏙️ Compare Cities")
        
        try:
            self.compare_panel = CityComparisonPanel(compare_frame, self.db, self.fetcher, self.logger)
        except Exception as e:
            self.logger.error(f"Error initializing compare panel: {e}")
            self._add_error_label(compare_frame, "🏙️ Compare Cities\n\nCity comparisons will appear here")

    def create_insights_tab(self):
        if not self.notebook:
            return
            
        try:            
            self.insights_panel = InsightsDashboardTab(
                parent_notebook=self.notebook,
                db=self.db,
                logger=self.logger,
                cfg=self.cfg,
                fetcher=self.fetcher,
                tracker=self.tracker
            )
            self.logger.info("Insights tab created successfully")
        except Exception as e:
            self.logger.error(f"Error creating insights tab: {e}")
           
            insights_frame = ttk.Frame(self.notebook)
            self.notebook.add(insights_frame, text="📈 Insights")
            self._add_error_label(insights_frame, "📈 Insights Dashboard\n\nInsights will appear here")
    
    def _add_error_label(self, parent: tk.Widget, message: str) -> None:
        error_label = tk.Label(
            parent, 
            text=message, 
            font=("Segoe UI", 16),
            bg="#f8fafc", 
            fg="#6b7280"
        )
        error_label.pack(expand=True)

    def get_notebook(self) -> Optional[ttk.Notebook]:    
        return self.notebook

    def refresh_all_panels(self) -> None:
        """Refresh all panels that support it"""
        try:
            # Check graphs panel
            if self.graphs_panel and hasattr(self.graphs_panel, 'refresh'):
                self.graphs_panel.refresh()
            
            # Check insights panel 
            if self.insights_panel:      
                if hasattr(self.insights_panel, 'trends_panel') and self.insights_panel.trends_panel:
                    if hasattr(self.insights_panel.trends_panel, 'refresh'):
                        self.insights_panel.trends_panel.refresh()
                
                if hasattr(self.insights_panel, 'stats_panel') and self.insights_panel.stats_panel:
                    if hasattr(self.insights_panel.stats_panel, 'refresh'):
                        self.insights_panel.stats_panel.refresh()
                
                if hasattr(self.insights_panel, 'activity_panel') and self.insights_panel.activity_panel:
                    if hasattr(self.insights_panel.activity_panel, 'refresh'):
                        self.insights_panel.activity_panel.refresh()
            
            # Check other panels
            if self.guess_panel and hasattr(self.guess_panel, 'refresh'):
                self.guess_panel.refresh()
                
            if self.compare_panel and hasattr(self.compare_panel, 'refresh'):
                self.compare_panel.refresh()
                    
        except Exception as e:
            self.logger.error(f"Error refreshing panels: {e}")

    def update_weather_data(self, weather_data: Any) -> None:
        """Update weather data in all relevant panels"""
        try:           
            if self.insights_panel:
                if hasattr(self.insights_panel, 'activity_panel') and self.insights_panel.activity_panel:
                    if hasattr(self.insights_panel.activity_panel, 'update_weather_data'):
                        self.insights_panel.activity_panel.update_weather_data(weather_data)
                
                if hasattr(self.insights_panel, 'stats_panel') and self.insights_panel.stats_panel:
                    if hasattr(self.insights_panel.stats_panel, 'update_weather_data'):
                        self.insights_panel.stats_panel.update_weather_data(weather_data)
                     
            if self.compare_panel and hasattr(self.compare_panel, 'update_weather_data'):
                self.compare_panel.update_weather_data(weather_data)
                    
        except Exception as e:
            self.logger.error(f"Error updating weather data in panels: {e}")

    def safe_panel_method_call(self, panel: Any, method_name: str, *args, **kwargs) -> bool:
        """Safely call a method on a panel if it exists"""
        try:
            if panel is not None and hasattr(panel, method_name):
                method = getattr(panel, method_name)
                if callable(method):
                    method(*args, **kwargs)
                    return True
                else:
                    self.logger.debug(f"Method {method_name} is not callable on {type(panel).__name__}")
            else:
                self.logger.debug(f"Panel {type(panel).__name__ if panel else 'None'} does not have method {method_name}")
            return False
        except Exception as e:
            self.logger.error(f"Error calling {method_name} on {type(panel).__name__ if panel else 'None'}: {e}")
            return False 
    
    def update_tomorrow_prediction_location(self, city, country):
        """Update tomorrow's prediction for new location - THIS IS THE KEY METHOD"""
        try:
            self.logger.info(f"Updating tomorrow prediction location to {city}, {country}")
            
            # Try multiple possible locations for the prediction panel
            prediction_updated = False
            
            # Check if it's in the guess panel
            if self.guess_panel and hasattr(self.guess_panel, 'update_location'):
                self.guess_panel.update_location(city, country)
                prediction_updated = True
                self.logger.info("Updated prediction via guess_panel")
            
            # Check if the prediction is in insights panel
            if self.insights_panel:
                # Try different possible nested structures
                if hasattr(self.insights_panel, 'guess_panel') and self.insights_panel.guess_panel:
                    if hasattr(self.insights_panel.guess_panel, 'update_location'):
                        self.insights_panel.guess_panel.update_location(city, country)
                        prediction_updated = True
                        self.logger.info("Updated prediction via insights_panel.guess_panel")
                
                # Try prediction_panel
                if hasattr(self.insights_panel, 'prediction_panel') and self.insights_panel.prediction_panel:
                    if hasattr(self.insights_panel.prediction_panel, 'update_location'):
                        self.insights_panel.prediction_panel.update_location(city, country)
                        prediction_updated = True
                        self.logger.info("Updated prediction via insights_panel.prediction_panel")
                
                # Try tomorrow_panel
                if hasattr(self.insights_panel, 'tomorrow_panel') and self.insights_panel.tomorrow_panel:
                    if hasattr(self.insights_panel.tomorrow_panel, 'update_location'):
                        self.insights_panel.tomorrow_panel.update_location(city, country)
                        prediction_updated = True
                        self.logger.info("Updated prediction via insights_panel.tomorrow_panel")
                
                # Try activity_panel (if it has prediction features)
                if hasattr(self.insights_panel, 'activity_panel') and self.insights_panel.activity_panel:
                    if hasattr(self.insights_panel.activity_panel, 'update_location'):
                        self.insights_panel.activity_panel.update_location(city, country)
                        prediction_updated = True
                        self.logger.info("Updated prediction via insights_panel.activity_panel")
            
            # Generic approach: try to update any panel that has update_location method
            panels_to_check = [
                ('graphs_panel', self.graphs_panel),
                ('compare_panel', self.compare_panel),
                ('insights_panel', self.insights_panel),
                ('guess_panel', self.guess_panel)
            ]
            
            for panel_name, panel in panels_to_check:
                if panel and hasattr(panel, 'update_location'):
                    try:
                        panel.update_location(city, country)
                        prediction_updated = True
                        self.logger.info(f"Updated prediction via {panel_name}")
                    except Exception as panel_error:
                        self.logger.warning(f"Failed to update {panel_name}: {panel_error}")
            
            # Also try to refresh any prediction-related content
            self.safe_panel_method_call(self.insights_panel, 'refresh_predictions', city, country)
            
            if prediction_updated:
                self.logger.info(f"Successfully updated tomorrow prediction location to {city}, {country}")
            else:
                self.logger.warning(f"Could not find prediction panel to update location to {city}, {country}")
                
        except Exception as e:
            self.logger.error(f"Error updating tomorrow prediction location: {e}")
    
    def update_location_for_all_panels(self, city, country):
        """Update location for all panels that support it"""
        try:
            self.logger.info(f"Updating all panels with new location: {city}, {country}")
            
            # List of panels and methods to try
            update_methods = [
                ('update_location', [city, country]),
                ('refresh_for_location', [city, country]),
                ('set_location', [city, country]),
                ('change_location', [city, country])
            ]
            
            panels = [
                ('graphs_panel', self.graphs_panel),
                ('compare_panel', self.compare_panel),
                ('insights_panel', self.insights_panel),
                ('guess_panel', self.guess_panel)
            ]
            
            for panel_name, panel in panels:
                if panel:
                    for method_name, args in update_methods:
                        if self.safe_panel_method_call(panel, method_name, *args):
                            self.logger.info(f"Updated {panel_name} with {method_name}")
                            break
            
            # Also update the tomorrow prediction specifically
            self.update_tomorrow_prediction_location(city, country)
            
        except Exception as e:
            self.logger.error(f"Error updating location for all panels: {e}")