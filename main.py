import tkinter as tk
from src.music_tracker import MusicTracker

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicTracker(root)
    root.mainloop()