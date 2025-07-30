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

        # Panel references - explicitly typed as Optional
        self.graphs_panel: Optional[Any] = None
        self.trends_panel: Optional[Any] = None
        self.stats_panel: Optional[Any] = None
        self.favorites_panel: Optional[Any] = None
        self.journal_panel: Optional[Any] = None
        self.guess_panel: Optional[Any] = None
        self.compare_panel: Optional[Any] = None
        self.activity_panel: Optional[Any] = None

        self.stats_display: Optional[tk.Frame] = None
        self.stats_label: Optional[tk.Label] = None

        # Notebook will be initialized in create_tab_interface
        self.notebook: Optional[ttk.Notebook] = None

    def create_tab_interface(self) -> ttk.Notebook:
        """Create the main tab notebook interface"""
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Create all tabs
        self.create_graphs_tab()
        self.create_trends_tab()
        self.create_statistics_tab()
        self.create_favorites_tab()
        self.create_journal_tab()
        self.create_guess_tab()
        self.create_compare_tab()
        self.create_activity_tab()

        return self.notebook

    def create_graphs_tab(self) -> None:
        """Create Charts & Graphs tab"""
        if not self.notebook:
            return
            
        graphs_frame = ttk.Frame(self.notebook)
        self.notebook.add(graphs_frame, text="📊 Charts & Graphs")
        
        try:
            self.graphs_panel = GraphsAndChartsPanel(graphs_frame, self.db, self.logger, self.theme_manager)
        except Exception as e:
            self.logger.error(f"Error initializing graphs panel: {e}")
            self._add_error_label(graphs_frame, "📊 Charts & Graphs\n\nGraphs panel will load here")

    def create_trends_tab(self) -> None:
        """Create Trends tab"""
        if not self.notebook:
            return
            
        trends_frame = ttk.Frame(self.notebook)
        self.notebook.add(trends_frame, text="📈 Trends")
        
        try:
            self.trends_panel = TrendPanel(trends_frame, self.db, self.logger, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing trends panel: {e}")
            self._add_error_label(trends_frame, "📈 Weather Trends\n\nTrends analysis will appear here")

    def create_statistics_tab(self) -> None:
        """Create Statistics tab"""
        if not self.notebook:
            return
            
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistics")
        
        try:
            self.stats_panel = SimpleStatsPanel(stats_frame, self.fetcher, self.db, self.logger, self.tracker, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing stats panel: {e}")
            self.create_manual_stats_display(stats_frame)

    def create_manual_stats_display(self, parent: tk.Widget) -> None:
        """Create manual statistics display when SimpleStatsPanel fails"""
        stats_container = tk.Frame(parent, bg="#f8fafc")
        stats_container.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = tk.Label(
            stats_container, 
            text="📊 Weather Statistics", 
            font=("Segoe UI", 20, "bold"),
            bg="#f8fafc", 
            fg="#1f2937"
        )
        title_label.pack(pady=(0, 20))

        controls_frame = tk.Frame(stats_container, bg="#f8fafc")
        controls_frame.pack(fill="x", pady=(0, 20))

        refresh_btn = tk.Button(
            controls_frame, 
            text="🔄 Refresh Stats", 
            font=("Segoe UI", 12, "bold"),
            bg="#3b82f6", 
            fg="white", 
            padx=20, 
            pady=10, 
            cursor="hand2", 
            command=self.show_statistics
        )
        refresh_btn.pack(side="left", padx=(0, 10))

        export_btn = tk.Button(
            controls_frame, 
            text="💾 Export Data", 
            font=("Segoe UI", 12, "bold"),
            bg="#f59e0b", 
            fg="white", 
            padx=20, 
            pady=10, 
            cursor="hand2",
            command=self.export_data_callback
        )
        export_btn.pack(side="left")

        self.stats_display = tk.Frame(stats_container, bg="white", relief="solid", bd=1)
        self.stats_display.pack(fill="both", expand=True)

        self.stats_label = tk.Label(
            self.stats_display, 
            text="Loading statistics...",
            font=("Segoe UI", 12), 
            bg="white", 
            fg="#374151"
        )
        self.stats_label.pack(padx=20, pady=20, anchor="w")

    def create_favorites_tab(self) -> None:
        """Create Favorites tab"""
        if not self.notebook:
            return
            
        favorites_frame = ttk.Frame(self.notebook)
        self.notebook.add(favorites_frame, text="⭐ Favorites")
        
        try:
            self.favorites_panel = FavoriteCityPanel(favorites_frame, self.tracker, self.db, self.logger, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing favorites panel: {e}")
            self._add_error_label(favorites_frame, "⭐ Favorite Cities\n\nFavorites manager will appear here")

    def create_journal_tab(self) -> None:
        """Create Journal tab"""
        if not self.notebook:
            return
            
        journal_frame = ttk.Frame(self.notebook)
        self.notebook.add(journal_frame, text="📓 Journal")
        
        try:
            self.journal_panel = JournalPanel(journal_frame, self.get_city_callback, self.logger, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing journal panel: {e}")
            self._add_error_label(journal_frame, "📓 Weather Journal\n\nJournal entries will appear here")

    def create_guess_tab(self) -> None:
        """Create Tomorrow's Guess tab"""
        if not self.notebook:
            return
            
        guess_frame = ttk.Frame(self.notebook)
        self.notebook.add(guess_frame, text="🔮 Tomorrow's Guess")
        
        try:
            self.guess_panel = TomorrowGuessPanel(guess_frame, self.db, self.logger, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing guess panel: {e}")
            self._add_error_label(guess_frame, "🔮 Tomorrow's Weather Guess\n\nPredictions will appear here")

    def create_compare_tab(self) -> None:
        """Create Compare Cities tab"""
        if not self.notebook:
            return
            
        compare_frame = ttk.Frame(self.notebook)
        self.notebook.add(compare_frame, text="🏙️ Compare Cities")
        
        try:
            self.compare_panel = CityComparisonPanel(compare_frame, self.db, self.fetcher, self.logger)
        except Exception as e:
            self.logger.error(f"Error initializing compare panel: {e}")
            self._add_error_label(compare_frame, "🏙️ Compare Cities\n\nCity comparisons will appear here")

    def create_activity_tab(self) -> None:
        """Create Activity Suggestions tab"""
        if not self.notebook:
            return
            
        activity_frame = ttk.Frame(self.notebook)
        self.notebook.add(activity_frame, text="🎯 Activity Suggestions")
        
        try:
            self.activity_panel = ActivityPanel(activity_frame, self.fetcher, self.db, self.logger, self.tracker, self.cfg)
        except Exception as e:
            self.logger.error(f"Error initializing activity panel: {e}")
            self._add_error_label(activity_frame, "🎯 Activity Suggestions\n\nActivity recommendations will appear here")

    def show_statistics(self) -> None:
        """Show weather statistics in the manual stats display"""
        try:
            city = self.get_city_callback()
            country = "US"
            stats_text = get_weather_stats(self.db, city, country)
            
            if self.stats_label:
                self.stats_label.config(text=f"📊 Statistics for {city}, {country}:\n\n{stats_text}")
                
        except Exception as e:
            self.logger.error(f"Error showing statistics: {e}")
            if self.stats_label:
                self.stats_label.config(text=f"Error loading statistics: {str(e)}")

    def _add_error_label(self, parent: tk.Widget, message: str) -> None:
        """Add error label to a tab when initialization fails"""
        error_label = tk.Label(
            parent, 
            text=message, 
            font=("Segoe UI", 16),
            bg="#f8fafc", 
            fg="#6b7280"
        )
        error_label.pack(expand=True)

    def get_notebook(self) -> Optional[ttk.Notebook]:
        """Get the notebook widget"""
        return self.notebook

    def refresh_all_panels(self) -> None:
        """Refresh all panels that support it"""
        try:
            # Check graphs panel
            if self.graphs_panel is not None:
                if hasattr(self.graphs_panel, 'refresh') and callable(getattr(self.graphs_panel, 'refresh')):
                    self.graphs_panel.refresh()
                else:
                    self.logger.debug("GraphsAndChartsPanel does not have a refresh method")
            
            # Check trends panel
            if self.trends_panel is not None:
                if hasattr(self.trends_panel, 'refresh') and callable(getattr(self.trends_panel, 'refresh')):
                    self.trends_panel.refresh()
                else:
                    self.logger.debug("TrendPanel does not have a refresh method")
            
            # Check stats panel
            if self.stats_panel is not None:
                if hasattr(self.stats_panel, 'refresh') and callable(getattr(self.stats_panel, 'refresh')):
                    self.stats_panel.refresh()
                else:
                    self.logger.debug("SimpleStatsPanel does not have a refresh method")
            else:
                # If no stats panel, refresh manual stats display
                self.show_statistics()
            
            # Check favorites panel
            if self.favorites_panel is not None:
                if hasattr(self.favorites_panel, 'refresh') and callable(getattr(self.favorites_panel, 'refresh')):
                    self.favorites_panel.refresh()
                else:
                    self.logger.debug("FavoriteCityPanel does not have a refresh method")
                    
        except Exception as e:
            self.logger.error(f"Error refreshing panels: {e}")

    def update_weather_data(self, weather_data: Any) -> None:
        """Update panels with new weather data"""
        try:
            # Check activity panel
            if self.activity_panel is not None:
                if hasattr(self.activity_panel, 'update_weather_data') and callable(getattr(self.activity_panel, 'update_weather_data')):
                    self.activity_panel.update_weather_data(weather_data)
                else:
                    self.logger.debug("ActivityPanel does not have an update_weather_data method")
            
            # Check stats panel
            if self.stats_panel is not None:
                if hasattr(self.stats_panel, 'update_weather_data') and callable(getattr(self.stats_panel, 'update_weather_data')):
                    self.stats_panel.update_weather_data(weather_data)
                else:
                    self.logger.debug("SimpleStatsPanel does not have an update_weather_data method")
                    
        except Exception as e:
            self.logger.error(f"Error updating weather data in panels: {e}")

    def safe_panel_method_call(self, panel: Any, method_name: str, *args, **kwargs) -> bool:
        """Safely call a method on a panel if it exists and is callable"""
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
            return False---