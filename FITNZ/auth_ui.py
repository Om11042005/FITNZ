# File: FITNZ/auth_ui.py

import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from .database import add_user, authenticate_user # <-- THIS LINE IS NOW CORRECTED

class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        login_frame = ttk.Frame(self); login_frame.grid(row=0, column=0)
        ttk.Label(login_frame, text="Fit NZ", font=("Helvetica", 36, "bold"), bootstyle="primary").pack(pady=20)
        role_frame = ttk.Labelframe(login_frame, text="Select Your Role", padding=15, bootstyle="info"); role_frame.pack(pady=20)
        self.selected_role = tk.StringVar()
        roles = ["Customer", "Employee", "Developer", "Manager", "Owner"]
        self.role_combobox = ttk.Combobox(role_frame, textvariable=self.selected_role, values=roles, state="readonly")
        self.role_combobox.set("Customer")
        self.role_combobox.pack(padx=10, pady=10, ipady=5, fill="x")
        entry_frame = ttk.Frame(login_frame); entry_frame.pack(pady=10, padx=40, fill="x")
        ttk.Label(entry_frame, text="Username").pack(anchor="w")
        self.username_entry = ttk.Entry(entry_frame, font=("Helvetica", 12)); self.username_entry.pack(pady=(0, 10), fill="x", ipady=5)
        ttk.Label(entry_frame, text="Password").pack(anchor="w")
        self.password_entry = ttk.Entry(entry_frame, font=("Helvetica", 12), show="*"); self.password_entry.pack(pady=(0, 10), fill="x", ipady=5)
        login_btn = ttk.Button(login_frame, text="Login", command=self.attempt_login, bootstyle="success-lg"); login_btn.pack(pady=(10,5), ipady=8, fill="x", padx=40)
        signup_btn = ttk.Button(login_frame, text="Don't have an account? Sign Up", command=self.open_signup, bootstyle="link-primary"); signup_btn.pack(pady=5)
        exit_btn = ttk.Button(login_frame, text="Exit Application", command=self.controller.confirm_exit, bootstyle="danger"); exit_btn.pack(pady=20, ipady=5, fill="x", padx=40)

    def attempt_login(self):
        username = self.username_entry.get(); password = self.password_entry.get(); role = self.selected_role.get()
        if not all([username, password, role]): Messagebox.show_error("Please select a role and enter your credentials.", "Login Failed", parent=self); return
        user = authenticate_user(username, password, role)
        if user: self.controller.show_main_app(user)
        else: Messagebox.show_error("Invalid credentials for the selected role.", "Login Failed", parent=self)

    def open_signup(self): signup_win = SignupPage(self); signup_win.grab_set()

class SignupPage(bs.Toplevel):
    def __init__(self, parent):
        super().__init__(parent); self.parent = parent; self.controller = parent.controller
        self.title("Customer Sign Up"); self.geometry("400x350"); self.resizable(False, False)
        frame = ttk.Frame(self, padding="20"); frame.pack(expand=True, fill="both")
        
        labels = ["Full Name:", "Contact (Email/Phone):", "Delivery Address:", "Username:", "Password:"]
        self.entries = {}
        for i, label in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, show="*" if label == "Password:" else "")
            entry.grid(row=i, column=1, sticky="ew")
            self.entries[label] = entry
            
        frame.grid_columnconfigure(1, weight=1)
        button_frame = ttk.Frame(frame); button_frame.grid(row=len(labels), column=0, columnspan=2, pady=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        ttk.Button(button_frame, text="Create Account", command=self.create_account, bootstyle="success").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(button_frame, text="Back", command=self.destroy, bootstyle="secondary-outline").grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def create_account(self):
        name = self.entries["Full Name:"].get(); contact = self.entries["Contact (Email/Phone):"].get()
        address = self.entries["Delivery Address:"].get(); username = self.entries["Username:"].get(); password = self.entries["Password:"].get()
        if not all([name, contact, address, username, password]): Messagebox.show_error("All fields are required.", "Error", parent=self); return

        if add_user(name, contact, username, password, "Customer", address):
            Messagebox.show_info("Account created successfully! You are now logged in.", "Success", parent=self)
            new_customer_obj = authenticate_user(username, password, "Customer")
            self.destroy(); self.controller.show_main_app(new_customer_obj)
        else: Messagebox.show_error("Username already exists.", "Error", parent=self)