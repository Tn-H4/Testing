import tkinter as tk
from datetime import datetime
import os

from screens.home import HomeScreen
from screens.settings import SettingsScreen
from screens.idle import IdleScreen
from screens.chat import ChatScreen
from shared.utils import time_strings
from shared.bot import ChatbotAssistant
from shared.camera import CameraManager

APP_W, APP_H, BAR_H = 1280, 720, 70
CYAN = "#70e2ff"
DARK_BG = "#2b2b2b"

class App(tk.Tk):
    def __init__(self, name_text="(name)"):
        super().__init__()
        self.title("TestingGUI")
        self.geometry(f"{APP_W}x{APP_H}")
        self.resizable(False, False)
        self.configure(bg=DARK_BG)

        self.camera = CameraManager(width=1280, height=720)
        self.name_text = name_text

        self.top = tk.Frame(self, bg=CYAN, highlightthickness=0)
        self.top.place(x=5, y=5, width=APP_W - 10, height=APP_H - BAR_H - 15)

        self.bar = tk.Frame(self, bg="black")
        self.bar.place(x=0, y=APP_H - BAR_H, width=APP_W, height=BAR_H)

        #chatbot
        base = os.path.dirname(os.path.abspath(__file__))
        intents_path = os.path.join(base, "intents.json")
        model_path   = os.path.join(base, "chatbot_model.pth")
        dims_path    = os.path.join(base, "dimensions.json")

        #Setting button
        self.gear_btn = tk.Button(
            self.bar, text="⚙", font=("Segoe UI Symbol", 20),
            fg="white", bg="black", bd=0, highlightthickness=0,
            activebackground="#222", command=self.toggle_settings
        )
        self.gear_btn.place(x=16, y=BAR_H // 2, anchor="w")

        #Home/Chat toggle button
        self.center_canvas = tk.Canvas(self.bar, width=42, height=42,
                                       bg="black", bd=0, highlightthickness=0, cursor="hand2")
        self.center_canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.center_canvas.create_oval(3, 3, 39, 39, fill="red", outline="red")
        self.center_canvas.bind("<Button-1>", lambda e: self.toggle_chat())

        #Time and date labels
        self.time_lbl = tk.Label(self.bar, text="", font=("Segoe UI", 14),
                                 fg="white", bg="black")
        self.date_lbl = tk.Label(self.bar, text="", font=("Segoe UI", 11),
                                 fg="white", bg="black")
        self.time_lbl.place(x=APP_W - 12, y=10, anchor="ne")
        self.date_lbl.place(x=APP_W - 12, y=BAR_H - 10, anchor="se")

        self.screens = {}
        self.current = None
        self._last_non_settings = "home"

        base = os.path.dirname(os.path.abspath(__file__))
        intents = os.path.join(base, "intents.json")
        model  = os.path.join(base, "chatbot_model.pth")
        dims   = os.path.join(base, "dimensions.json")

        self.assistant = ChatbotAssistant(intents_path=intents, model_path=model, dimensions_path=dims)
        
        self.register_screen("home", HomeScreen(self.top, self))
        self.register_screen("settings", SettingsScreen(self.top, self))
        self.register_screen("idle", IdleScreen(self.top, self))
        self.register_screen("chat", ChatScreen(self.top, self, assistant=self.assistant))

        #Timeout counting
        self.idle_ms = 10_000
        self._idle_after = None
        self._install_activity_hooks()

        #First show
        self.show("home")
        self.update_clock()
        self._reset_idle_timer()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    #Each screen is positioned to fill top, then hidden.
    def register_screen(self, name, frame):
        self.screens[name] = frame
        frame.place(x=0, y=0, relwidth=1, relheight=1)
        frame.place_forget()

    def show(self, name):
        if self.current:
            self.screens[self.current].on_hide()
            self.screens[self.current].place_forget()

        if name != "settings":
            self._last_non_settings = name

        self.current = name
        self.screens[name].place(x=0, y=0, relwidth=1, relheight=1)
        self.screens[name].on_show()

        #update the setting button when in SettingScreen
        self.gear_btn.config(text="⟵" if name == "settings" else "⚙")
        self._reset_idle_timer()

    def toggle_settings(self):
        if self.current == "settings":
            self.show(self._last_non_settings)
        else:
            self.show("settings")

    def toggle_chat(self):
        if self.current == "chat":
            # Always return to Home
            self.show("home")
        else:
            self.show("chat")

    def update_clock(self):
        now = datetime.now()
        t_str, d_str = time_strings(now)
        self.time_lbl.config(text=t_str)
        self.date_lbl.config(text=d_str)
        self.after(1000, self.update_clock)

    #Idle detection
    def _install_activity_hooks(self):
        for seq in ("<Motion>", "<Button>", "<Key>"):
            self.bind_all(seq, self.on_activity, add="+")

    def _reset_idle_timer(self):
        if getattr(self, "_idle_after", None) is not None:
            try:
                self.after_cancel(self._idle_after)
            except Exception:
                pass
        if self.current != "idle":
            self._idle_after = self.after(self.idle_ms, self._go_idle)

    def _go_idle(self):
        self.show("idle")
        self.camera.release()

    def on_activity(self, event=None):
        if self.current == "idle":
            self.show("home")
            self.camera.open()

        else:
            self._reset_idle_timer()

    def on_close(self):
        self.camera.release()
        self.destroy()

if __name__ == "__main__":
    App(name_text="(name)").mainloop()
