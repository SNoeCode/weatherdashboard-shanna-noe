import os
from PIL import Image, ImageTk
import tkinter as tk

class WeatherGifAnimator:
    def __init__(self, parent, weather_folder, delay=100):
        self.parent = parent
        self.weather_folder = weather_folder
        self.delay = delay
        self.label = tk.Label(parent)
        self.label.pack()
        self.frames = []
        self._load_frames()
        self._animate()

    def _load_frames(self):
        self.frames = []
        for fname in sorted(os.listdir(self.weather_folder)):
            if fname.endswith(".gif"):
                img = Image.open(os.path.join(self.weather_folder, fname))
                self.frames.append(ImageTk.PhotoImage(img))

    def _animate(self, i=0):
        if not self.frames:
            return
        self.label.config(image=self.frames[i])
        self.label.image = self.frames[i]
        self.parent.after(self.delay, self._animate, (i + 1) % len(self.frames))

    def change_weather(self, new_folder):
        self.weather_folder = new_folder
        self._load_frames()                                                                                                   
        
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Weather Animation")

    sorted_base = r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\icons\sorted"
    animator = WeatherGifAnimator(root, os.path.join(sorted_base, "sunny"))

    root.mainloop()