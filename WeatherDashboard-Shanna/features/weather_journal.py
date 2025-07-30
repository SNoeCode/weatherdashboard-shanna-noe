# features/journal_panel.py

import tkinter as tk
from tkinter import ttk, messagebox
from features.save_weather_journal import save_journal_entry  # standalone save function

class JournalPanel:
    def __init__(self, parent_tab, get_city_callback,logger, cfg):
        self.get_city_callback = get_city_callback

        self.frame = ttk.Frame(parent_tab, padding=20)
        self.frame.pack(expand=True, fill='both')

        ttk.Label(self.frame, text="Mood:", font=("Segoe UI", 12)).pack(pady=5)
        self.mood_entry = ttk.Entry(self.frame, width=40)
        self.mood_entry.pack(pady=5)

        ttk.Label(self.frame, text="Note:", font=("Segoe UI", 12)).pack(pady=5)
        self.note_entry = ttk.Entry(self.frame, width=60)
        self.note_entry.pack(pady=5)

        ttk.Button(self.frame, text="Save Entry", command=self.save_entry).pack(pady=15)

                       
    def save_entry(self):
        mood = self.mood_entry.get().strip()
        note = self.note_entry.get().strip()
        city = self.get_city_callback()

        if mood and note and city:
            save_journal_entry(city, mood, note)
            messagebox.showinfo("✅ Saved", f"Journal entry saved for {city}.")
            self.mood_entry.delete(0, tk.END)
            self.note_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("⚠️ Missing Info", "Fill out all fields before saving.")
        