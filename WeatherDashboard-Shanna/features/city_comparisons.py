from tkinter import ttk
from features.simple_statisitics import get_weather_stats 


def setup_comparison_tab(gui):
    frame = ttk.Frame(gui.compare_tab, padding=20)
    frame.pack(expand=True)

    ttk.Label(frame, text="🌇 City A:").grid(row=0, column=0, sticky="e")
    gui.city1_entry = ttk.Entry(frame, width=25)
    gui.city1_entry.grid(row=0, column=1, padx=5)

    ttk.Label(frame, text="🌆 City B:").grid(row=1, column=0, sticky="e")
    gui.city2_entry = ttk.Entry(frame, width=25)
    gui.city2_entry.grid(row=1, column=1, padx=5)

    ttk.Button(frame, text="🔍 Compare", command=gui.compare_cities).grid(row=2, column=0, columnspan=2, pady=10)

    gui.compare_frame = ttk.LabelFrame(frame, text="City Comparison", padding=10)
    gui.compare_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)