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
 