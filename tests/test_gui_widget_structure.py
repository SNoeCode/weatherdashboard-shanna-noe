def test_gui_widget_structure():
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    search_frame = ttk.LabelFrame(root, text="SearchBar")
    search_frame.pack()
    assert isinstance(search_frame, ttk.LabelFrame)

