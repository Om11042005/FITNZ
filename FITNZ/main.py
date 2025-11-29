# File: FITNZ/main.py
"""
Fit NZ - Retail POS System
Main application controller for managing window navigation and lifecycle.
"""

import ttkbootstrap as bs
from ttkbootstrap.dialogs import Messagebox
from . import database_mysql as db
from .auth_ui import LoginPage
from .main_app_ui import MainAppPage  # This should now work


# ===============================================
# Code Owner: Om (Initial Developer/Core Structure)
# US: Core system initialization, window control.
# ===============================================


class AppController(bs.Window):
    """Main application window controller managing page navigation."""
    
    def __init__(self):
        super().__init__(themename="cyborg")
        self.title("Fit NZ - Fitness Equipment & Nutrition")
        self.minsize(500, 600)
        self.protocol("WM_DELETE_WINDOW", self.confirm_exit)
        
        # Configure main window grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.current_frame = None
        self.show_login_page()
        
        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def show_frame(self, FrameClass, *args, **kwargs):
        """Smoothly transition between frames."""
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = FrameClass(self, self, *args, **kwargs)
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.tkraise()
        self.update_idletasks()

    def show_login_page(self):
        """Display the login page."""
        self.title("Fit NZ - Login")
        self.minsize(500, 600)
        
        # Reset window state
        try:
            self.state('normal')
        except:
            pass
        
        self.geometry("550x700")
        self.show_frame(LoginPage)

    def show_main_app(self, user):
        """Display the main application interface based on user role."""
        self.title(f"Fit NZ - Retail POS System | {user.get_name() if hasattr(user, 'get_name') else getattr(user, 'name', 'User')}")
        self.minsize(1200, 800)
        
        # Maximize window for main app
        try:
            self.state('zoomed')
        except:
            # Fallback for systems that don't support 'zoomed'
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            self.geometry(f"{screen_width}x{screen_height}")
        
        self.show_frame(MainAppPage, logged_in_user=user)

    def confirm_exit(self):
        """Confirm before exiting the application."""
        result = Messagebox.yesno(
            "Are you sure you want to exit Fit NZ?", 
            "Exit Confirmation", 
            parent=self
        )
        if result == "Yes":
            self.destroy()

# Om/Imran: Database setup must run first


if __name__ == "__main__":
    try:
        db.setup_database()
        app = AppController()
        app.mainloop()
    except Exception as e:
        # Imran: General error handling/reporting for system stability
        Messagebox.show_error(
            f"Failed to start application: {str(e)}", 
            "Startup Error"
        )