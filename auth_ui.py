# File: FITNZ/auth_ui.py

import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from .database import add_user, authenticate_user

class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure grid for centering
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main container with padding
        main_container = ttk.Frame(self, padding=30)
        main_container.grid(row=0, column=0, sticky="")
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Brand header
        brand_frame = ttk.Frame(main_container)
        brand_frame.pack(pady=(0, 30))
        
        ttk.Label(
            brand_frame, 
            text="🏋️ Fit NZ", 
            font=("Segoe UI", 42, "bold"), 
            bootstyle="primary"
        ).pack()
        
        ttk.Label(
            brand_frame, 
            text="Fitness Equipment & Nutrition", 
            font=("Segoe UI", 11), 
            bootstyle="secondary"
        ).pack(pady=(5, 0))
        
        # Login card with better styling
        login_card = ttk.Labelframe(
            main_container, 
            text="Login to Your Account", 
            padding=30, 
            bootstyle="info"
        )
        login_card.pack(fill="x", padx=20)
        
        # Role selection
        role_frame = ttk.Frame(login_card)
        role_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            role_frame, 
            text="Role:", 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.selected_role = tk.StringVar()
        roles = ["Customer", "Employee", "Developer", "Manager", "Owner"]
        self.role_combobox = ttk.Combobox(
            role_frame, 
            textvariable=self.selected_role, 
            values=roles, 
            state="readonly",
            font=("Segoe UI", 11)
        )
        self.role_combobox.set("Customer")
        self.role_combobox.pack(fill="x", ipady=6)
        
        # Username field
        username_frame = ttk.Frame(login_card)
        username_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            username_frame, 
            text="Username:", 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.username_entry = ttk.Entry(
            username_frame, 
            font=("Segoe UI", 11)
        )
        self.username_entry.pack(fill="x", ipady=8)
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        
        # Password field
        password_frame = ttk.Frame(login_card)
        password_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            password_frame, 
            text="Password:", 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.password_entry = ttk.Entry(
            password_frame, 
            font=("Segoe UI", 11), 
            show="●"
        )
        self.password_entry.pack(fill="x", ipady=8)
        self.password_entry.bind('<Return>', lambda e: self.attempt_login())
        
        # Action buttons
        button_frame = ttk.Frame(login_card)
        button_frame.pack(fill="x", pady=(10, 0))
        
        login_btn = ttk.Button(
            button_frame, 
            text="Login", 
            command=self.attempt_login, 
            bootstyle="success",
            width=20
        )
        login_btn.pack(fill="x", ipady=10, pady=(0, 10))
        
        signup_btn = ttk.Button(
            button_frame, 
            text="Create New Account", 
            command=self.open_signup, 
            bootstyle="primary-outline",
            width=20
        )
        signup_btn.pack(fill="x", ipady=8, pady=(0, 10))
        
        exit_btn = ttk.Button(
            button_frame, 
            text="Exit Application", 
            command=self.controller.confirm_exit, 
            bootstyle="danger-outline",
            width=20
        )
        exit_btn.pack(fill="x", ipady=8)
        
        # Focus on username entry when page loads
        self.username_entry.focus_set()

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        role = self.selected_role.get()
        
        if not username:
            Messagebox.show_error(
                "Please enter your username.", 
                "Login Failed", 
                parent=self
            )
            self.username_entry.focus_set()
            return
        
        if not password:
            Messagebox.show_error(
                "Please enter your password.", 
                "Login Failed", 
                parent=self
            )
            self.password_entry.focus_set()
            return
        
        if not role:
            Messagebox.show_error(
                "Please select your role.", 
                "Login Failed", 
                parent=self
            )
            return
        
        user = authenticate_user(username, password, role)
        if user:
            self.controller.show_main_app(user)
        else:
            Messagebox.show_error(
                "Invalid credentials for the selected role. Please check your username, password, and role.", 
                "Login Failed", 
                parent=self
            )
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()

    def open_signup(self):
        signup_win = SignupPage(self)
        signup_win.grab_set()

class SignupPage(bs.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.controller = parent.controller
        
        self.title("Create New Account - Fit NZ")
        self.geometry("480x550")
        self.resizable(False, False)
        self.transient(parent)
        
        # Main container
        main_frame = ttk.Frame(self, padding=25)
        main_frame.pack(expand=True, fill="both")
        
        # Header
        ttk.Label(
            main_frame, 
            text="Create New Account", 
            font=("Segoe UI", 20, "bold"), 
            bootstyle="primary"
        ).pack(pady=(0, 10))
        
        ttk.Label(
            main_frame, 
            text="Join Fit NZ and start your fitness journey", 
            font=("Segoe UI", 9), 
            bootstyle="secondary"
        ).pack(pady=(0, 25))
        
        # Form fields
        labels = [
            "Full Name:",
            "Contact (Email/Phone):",
            "Delivery Address:",
            "Username:",
            "Password:"
        ]
        
        self.entries = {}
        field_frame = ttk.Frame(main_frame)
        field_frame.pack(fill="both", expand=True)
        field_frame.grid_columnconfigure(1, weight=1)
        
        for i, label in enumerate(labels):
            # Label
            label_widget = ttk.Label(
                field_frame, 
                text=label, 
                font=("Segoe UI", 10, "bold")
            )
            label_widget.grid(row=i, column=0, sticky="w", pady=8, padx=(0, 15))
            
            # Entry field
            is_password = label == "Password:"
            entry = ttk.Entry(
                field_frame, 
                show="●" if is_password else "",
                font=("Segoe UI", 10),
                width=30
            )
            entry.grid(row=i, column=1, sticky="ew", pady=8, ipady=6)
            self.entries[label] = entry
        
        # Set focus navigation
        entries_list = list(self.entries.values())
        for i, entry in enumerate(entries_list):
            if i < len(entries_list) - 1:
                entry.bind('<Return>', lambda e, next_entry=entries_list[i+1]: next_entry.focus())
            else:
                entry.bind('<Return>', lambda e: self.create_account())
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        ttk.Button(
            button_frame, 
            text="Create Account", 
            command=self.create_account, 
            bootstyle="success"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=8)
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self.destroy, 
            bootstyle="secondary-outline"
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0), ipady=8)
        
        # Focus on first field
        entries_list[0].focus_set()

    def create_account(self):
        name = self.entries["Full Name:"].get().strip()
        contact = self.entries["Contact (Email/Phone):"].get().strip()
        address = self.entries["Delivery Address:"].get().strip()
        username = self.entries["Username:"].get().strip()
        password = self.entries["Password:"].get()
        
        # Validation
        if not name:
            Messagebox.show_error("Please enter your full name.", "Validation Error", parent=self)
            self.entries["Full Name:"].focus_set()
            return
        
        if not contact:
            Messagebox.show_error("Please enter your contact information (email or phone).", "Validation Error", parent=self)
            self.entries["Contact (Email/Phone):"].focus_set()
            return
        
        if not address:
            Messagebox.show_error("Please enter your delivery address.", "Validation Error", parent=self)
            self.entries["Delivery Address:"].focus_set()
            return
        
        if not username:
            Messagebox.show_error("Please choose a username.", "Validation Error", parent=self)
            self.entries["Username:"].focus_set()
            return
        
        if len(username) < 3:
            Messagebox.show_error("Username must be at least 3 characters long.", "Validation Error", parent=self)
            self.entries["Username:"].focus_set()
            return
        
        if not password:
            Messagebox.show_error("Please enter a password.", "Validation Error", parent=self)
            self.entries["Password:"].focus_set()
            return
        
        if len(password) < 4:
            Messagebox.show_error("Password must be at least 4 characters long.", "Validation Error", parent=self)
            self.entries["Password:"].focus_set()
            return

        if add_user(name, contact, username, password, "Customer", address):
            Messagebox.show_info(
                "Account created successfully! You are now logged in.", 
                "Success", 
                parent=self
            )
            new_customer_obj = authenticate_user(username, password, "Customer")
            self.destroy()
            self.controller.show_main_app(new_customer_obj)
        else:
            Messagebox.show_error(
                "Username already exists. Please choose a different username.", 
                "Error", 
                parent=self
            )
            self.entries["Username:"].delete(0, tk.END)
            self.entries["Username:"].focus_set()