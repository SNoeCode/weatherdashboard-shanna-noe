from tkinter import ttk
import tkinter as tk

class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.current_theme = "dark"  
        self.style = ttk.Style()
        self.theme_callbacks = [] 
        
    
        self.themes = {
            "dark": {
                "bg_primary": "#1e40af",
                "bg_secondary": "#1e3a8a", 
                "bg_card": "#374151",
                "bg_surface": "#1f2937",
                "text_primary": "#ffffff",
                "text_secondary": "#9ca3af",
                "text_muted": "#6b7280",
                "accent": "#3b82f6",
                "accent_hover": "#2563eb",
                "border": "#374151",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444"
            },
            "light": {
                "bg_primary": "#f8fafc",
                "bg_secondary": "#ffffff",
                "bg_card": "#ffffff", 
                "bg_surface": "#f1f5f9",
                "text_primary": "#111827",
                "text_secondary": "#374151",
                "text_muted": "#6b7280",
                "accent": "#3b82f6",
                "accent_hover": "#2563eb",
                "border": "#e5e7eb",
                "success": "#059669",
                "warning": "#d97706",
                "error": "#dc2626"
            }
        }
        
        # Apply theme
        self.apply_theme(self.current_theme)
    
    def get_theme_colors(self):
        """Current theme color palette"""
        return self.themes[self.current_theme]
    
    def register_callback(self, callback):
        """Callback function to be called when theme changes"""
        self.theme_callbacks.append(callback)
    
    def apply_theme(self, mode):      
        if mode not in self.themes:
            return
            
        colors = self.themes[mode]
        
        # Configure root window
        self.root.configure(bg=colors["bg_primary"])
        
        # Configure ttk styles
        self.style.configure("Modern.TFrame", 
                           background=colors["bg_primary"], 
                           relief="flat")
        
        self.style.configure("Card.TFrame", 
                           background=colors["bg_card"], 
                           relief="flat")
        
        self.style.configure("Surface.TFrame", 
                           background=colors["bg_surface"], 
                           relief="flat")
        
        self.style.configure("Header.TLabel", 
                           background=colors["bg_primary"], 
                           foreground=colors["text_primary"], 
                           font=("Segoe UI", 14, "bold"))
        
        self.style.configure("Title.TLabel", 
                           background=colors["bg_card"], 
                           foreground=colors["text_primary"], 
                           font=("Segoe UI", 16, "bold"))
        
        self.style.configure("Body.TLabel", 
                           background=colors["bg_card"], 
                           foreground=colors["text_secondary"], 
                           font=("Segoe UI", 10))
        
        self.style.configure("Muted.TLabel", 
                           background=colors["bg_card"], 
                           foreground=colors["text_muted"], 
                           font=("Segoe UI", 9))
        
        self.style.configure("Modern.TButton", 
                           font=("Segoe UI", 10, "bold"), 
                           foreground="white", 
                           background=colors["accent"],
                           borderwidth=0,
                           focuscolor='none',
                           padding=(15, 8))
        
        self.style.map("Modern.TButton",
                      background=[('active', colors["accent_hover"]),
                                ('pressed', colors["accent"])])
        
        self.style.configure("Success.TButton", 
                           font=("Segoe UI", 9, "bold"), 
                           foreground="white", 
                           background=colors["success"],
                           borderwidth=0,
                           padding=(10, 6))
        
        self.style.configure("Warning.TButton", 
                           font=("Segoe UI", 9, "bold"), 
                           foreground="white", 
                           background=colors["warning"],
                           borderwidth=0,
                           padding=(10, 6))
        
        self.style.configure("Search.TEntry", 
                           fieldbackground=colors["bg_surface"], 
                           foreground=colors["text_primary"],
                           borderwidth=1,
                           bordercolor=colors["border"],
                           insertcolor=colors["text_primary"],
                           padding=8)
        
        self.style.configure("Modern.TNotebook", 
                           background=colors["bg_primary"],
                           borderwidth=0)
        
        self.style.configure("Modern.TNotebook.Tab", 
                           background=colors["bg_surface"],
                           foreground=colors["text_secondary"],
                           padding=[12, 8],
                           borderwidth=0)
        
        self.style.map("Modern.TNotebook.Tab",
                      background=[('selected', colors["bg_card"]),
                                ('active', colors["accent"])],
                      foreground=[('selected', colors["text_primary"]),
                                ('active', 'white')])
        
        # Update theme
        self.current_theme = mode
        
        # Call all registered callbacks
        for callback in self.theme_callbacks:
            try:
                callback(colors)
            except Exception as e:
                print(f"Theme callback error: {e}")
    
    def toggle_theme(self):
        new_mode = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(new_mode)
        return new_mode
    
    def is_dark_theme(self):
        """Check if current theme is dark"""
        return self.current_theme == "dark"
    
    def get_contrast_color(self, base_color):
        colors = self.get_theme_colors()
        return colors["text_primary"] if self.current_theme == "dark" else colors["text_secondary"]