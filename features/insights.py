from tkinter import ttk
from features.simple_statistics import SimpleStatsPanel
from features.tomorrows_guess import TomorrowGuessPanel
from features.activity.activity_panel import ActivityPanel
from features.trends import TrendPanel
from services.weather_stats import get_weather_stats
import tkinter as tk

class InsightsDashboardTab:
    def __init__(self, parent_notebook, db, logger, cfg, fetcher, tracker):
        self.db = db
        self.logger = logger
        self.cfg = cfg
        self.fetcher = fetcher
        self.tracker = tracker
        self.parent_notebook = parent_notebook

        self.setup_styles()
        self.create_tab()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Custom.TNotebook',
                        background='#f0f4f8',
                        borderwidth=0)
        style.configure('Custom.TNotebook.Tab',
                        background='#e2e8f0',
                        foreground='#2d3748',
                        padding=[20, 12],
                        font=('Segoe UI', 11, 'bold'))
        style.map('Custom.TNotebook.Tab',
                  background=[('selected', '#667eea'), ('active', '#764ba2')],
                  foreground=[('selected', '#ffffff'), ('active', '#ffffff')])
        style.configure('Gradient.TFrame', background='#667eea')
        style.configure('Card.TFrame',
                        background='#ffffff',
                        relief='flat',
                        borderwidth=1)
        style.configure('Section.TLabelframe',
                        background='#ffffff',
                        foreground='#2d3748',
                        font=('Segoe UI', 12, 'bold'))

    def create_tab(self):
        insights_frame = tk.Frame(self.parent_notebook, bg='#f1f5f9')
        self.parent_notebook.add(insights_frame, text='📈 Stats and Trends Insights')

        # Three-column layout
        insights_frame.columnconfigure(0, weight=4)  # Stats/Trends panel
        insights_frame.columnconfigure(1, weight=3)  # Tomorrow prediction
        insights_frame.columnconfigure(2, weight=3)  # Activity panel
        insights_frame.rowconfigure(0, weight=1)

        # Create the three main frames
        stats_frame = tk.Frame(insights_frame, bg='#f8fafc', relief='solid', bd=1)
        tomorrow_frame = tk.Frame(insights_frame, bg='#0f0f23', relief='solid', bd=1)
        activity_frame = tk.Frame(insights_frame, bg='#fef2f2', relief='solid', bd=1)

        # Grid the frames
        stats_frame.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        tomorrow_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=10)
        activity_frame.grid(row=0, column=2, sticky='nsew', padx=(5, 10), pady=10)

        # LEFT PANEL: Stats with Trends as tabbed interface
        try:
            # Create notebook for stats and trends tabs
            self.stats_notebook = ttk.Notebook(stats_frame, style='Custom.TNotebook')
            self.stats_notebook.pack(expand=True, fill='both', padx=5, pady=5)
            
            # Statistics tab
            stats_tab_frame = tk.Frame(self.stats_notebook, bg='#f8fafc')
            self.stats_notebook.add(stats_tab_frame, text='📊 Statistics')
            self.stats_panel = SimpleStatsPanel(stats_tab_frame, self.fetcher, self.db, self.logger, self.tracker, self.cfg)
            
            # Trends tab
            trends_tab_frame = tk.Frame(self.stats_notebook, bg='#f0fdf4')
            self.stats_notebook.add(trends_tab_frame, text='📈 Trends')
            self.trends_panel = TrendPanel(trends_tab_frame, self.db, self.logger, self.cfg)
            
            self.logger.info("Stats and Trends panels loaded successfully")
        except Exception as e:
            self.logger.error(f"Stats/Trends panel error: {e}")
            self.create_placeholder(stats_frame, "Statistics and trends loading...", "#3b82f6")

        # MIDDLE PANEL: Tomorrow's prediction
        try:
            self.tomorrow_panel = TomorrowGuessPanel(tomorrow_frame, self.db, self.logger, self.cfg)
            self.logger.info("TomorrowGuessPanel loaded successfully")
        except Exception as e:
            self.logger.error(f"TomorrowGuessPanel error: {e}")
            self.create_placeholder(tomorrow_frame, "Tomorrow prediction unavailable.", "#007AFF")

        # RIGHT PANEL: Activity suggestions
        try:
            self.activity_panel = ActivityPanel(activity_frame, self.fetcher, self.db, self.logger, self.tracker, self.cfg)
            self.logger.info("ActivityPanel loaded successfully")
        except Exception as e:
            self.logger.error(f"ActivityPanel error: {e}")
            self.create_placeholder(activity_frame, "Activity suggestions loading...", "#dc2626")

    def create_placeholder(self, parent, text, color):
        """Create a placeholder when a panel fails to load"""
        placeholder = tk.Frame(parent, bg=parent['bg'])
        placeholder.pack(expand=True, fill='both')
        
        content_frame = tk.Frame(placeholder, bg=parent['bg'])
        content_frame.pack(expand=True, pady=40)
        
        icon = tk.Label(content_frame, text="⚠️", font=("Segoe UI", 36), fg=color, bg=parent['bg'])
        icon.pack(pady=(0, 10))
        
        message = tk.Label(content_frame, text=text, font=("Segoe UI", 12), fg=color, bg=parent['bg'],
                          wraplength=200, justify='center')
        message.pack()
        
        retry_btn = tk.Button(content_frame, text="🔄 Retry", font=("Segoe UI", 10, 'bold'),
                             bg=color, fg='white', relief='flat', padx=20, pady=5,
                             command=lambda: self.retry_panel_load(parent))
        retry_btn.pack(pady=(10, 0))
    
    def retry_panel_load(self, parent):
        """Attempt to reload a failed panel"""
        self.logger.info("Retrying panel load...")
        pass