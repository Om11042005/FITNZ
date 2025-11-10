# File: FITNZ/main.py
import ttkbootstrap as bs
from ttkbootstrap.dialogs import Messagebox
from . import database as db  # Corrected Import
from .auth_ui import LoginPage
from .main_app_ui import MainAppPage

class AppController(bs.Window):
    def __init__(self):
        super().__init__(themename="cyborg")
        self.title("Fit NZ")
        self.minsize(500, 600)
        self.protocol("WM_DELETE_WINDOW", self.confirm_exit)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.current_frame = None
        self.show_login_page()

    def show_frame(self, FrameClass, *args, **kwargs):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = FrameClass(self, self, *args, **kwargs)
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.tkraise()

    def show_login_page(self):
        self.title("Fit NZ - Login")
        self.minsize(500, 600)
        self.state('normal') 
        self.geometry("500x600")
        self.show_frame(LoginPage)

    def show_main_app(self, user):
        self.title("Fit NZ - Retail Management System")
        self.minsize(1200, 800)
        self.state('zoomed')
        self.show_frame(MainAppPage, logged_in_user=user)

    def confirm_exit(self):
        if Messagebox.yesno("Are you sure you want to exit?", "Exit Confirmation", parent=self):
            self.destroy()

if __name__ == "__main__":
    db.setup_database()
    app = AppController()
    app.mainloop()