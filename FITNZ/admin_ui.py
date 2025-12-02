# File: FITNZ/admin_ui.py
import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from . import database_mysql as db

# ===============================================
# Code Owner: Imran (US: Admin Panel for managing users)
# This entire file is owned by Imran's US.
# ===============================================

class AdminPage(bs.Toplevel):
    def __init__(self, parent, logged_in_user):
        super().__init__(parent)
        self.logged_in_user = logged_in_user
        self.title("⚙️ Admin Panel - User Management - Fit NZ")
        self.minsize(750, 600)
        self.transient(parent)

        # Header with improved styling
        header_frame = ttk.Frame(self, padding=(20, 15, 20, 15), bootstyle="secondary")
        header_frame.pack(fill="x")
        
        ttk.Label(
            header_frame, 
            text="⚙️ User Management", 
            font=("Segoe UI", 18, "bold"), 
            bootstyle="inverse-secondary"
        ).pack(side="left")
        
        ttk.Label(
            header_frame, 
            text=f"Logged in as: {logged_in_user.name}", 
            font=("Segoe UI", 9),
            bootstyle="inverse-secondary"
        ).pack(side="right")

        # Main content frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # User tree frame
        tree_frame = ttk.Labelframe(
            main_frame, 
            text="👥 All Users", 
            padding=15, 
            bootstyle="info"
        )
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Treeview container
        tree_container = ttk.Frame(tree_frame)
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        cols = ("ID", "Username", "Role", "Name")
        self.user_tree = ttk.Treeview(
            tree_container, 
            columns=cols, 
            show="headings", 
            bootstyle="primary",
            selectmode="browse"
        )
        
        # Configure columns
        self.user_tree.heading("ID", text="User ID", anchor="center")
        self.user_tree.column("ID", width=80, stretch=False, anchor="center")
        self.user_tree.heading("Username", text="Username", anchor="w")
        self.user_tree.column("Username", width=150, anchor="w")
        self.user_tree.heading("Role", text="Role", anchor="center")
        self.user_tree.column("Role", width=120, stretch=False, anchor="center")
        self.user_tree.heading("Name", text="Full Name", anchor="w")
        self.user_tree.column("Name", width=200, anchor="w")
        
        self.user_tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_container, 
            orient="vertical", 
            command=self.user_tree.yview, 
            bootstyle="secondary-round"
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        # Load users
        self.load_users()

        # Action buttons
        action_frame = ttk.Frame(tree_frame)
        action_frame.grid(row=0, column=1, sticky="ns", padx=(15, 0))
        
        ttk.Button(
            action_frame, 
            text="➕ Add User", 
            command=self.open_add_user, 
            bootstyle="success-outline",
            width=18
        ).pack(pady=(0, 10), fill="x")
        
        ttk.Button(
            action_frame, 
            text="🗑️ Delete User", 
            command=self.delete_user, 
            bootstyle="danger",
            width=18
        ).pack(pady=10, fill="x")
        
        # Back button
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=(15, 0), sticky="e")
        
        ttk.Button(
            button_frame, 
            text="← Back", 
            command=self.destroy, 
            bootstyle="secondary-outline",
            width=15
        ).pack(side="right")

    def open_add_user(self):
        add_win = AddUserPage(self, self.logged_in_user)
        add_win.grab_set()

    def load_users(self):
        for i in self.user_tree.get_children(): 
            self.user_tree.delete(i)
        for user in db.get_all_users():
            user_id = getattr(user, 'employee_id', getattr(user, '_customer_id', 'N/A'))
            name = getattr(user, 'name', getattr(user, '_name', 'N/A'))
            self.user_tree.insert("", "end", iid=user_id, values=(user_id, user.username, user.role, name))

    def delete_user(self):
        selected_item_id = self.user_tree.focus()
        if not selected_item_id: 
            Messagebox.show_warning("Please select a user to delete.", "No Selection", parent=self)
            return
        if selected_item_id == "E001": 
            Messagebox.show_error("Cannot delete the primary developer account.", "Error", parent=self)
            return
        if Messagebox.yesno(f"Are you sure you want to delete user ID {selected_item_id}?", "Confirm Deletion", parent=self):
            if db.delete_user_by_id(selected_item_id):
                Messagebox.show_info("User deleted successfully.", "Success", parent=self)
                self.load_users()
            else: 
                Messagebox.show_error("Failed to delete user.", "Error", parent=self)

class AddUserPage(bs.Toplevel):
    def __init__(self, parent, logged_in_user):
        super().__init__(parent)
        self.parent = parent
        self.logged_in_user = logged_in_user
        self.title("➕ Add New User - Fit NZ")

        # Increase height so buttons are not cut
        self.geometry("600x600")
        self.resizable(False, False)
        self.transient(parent)

        # MAIN container (PACK)
        main = ttk.Frame(self, padding=25)
        main.pack(expand=True, fill="both")

        # Header
        ttk.Label(
            main,
            text="➕ Add New User",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).pack(pady=(0, 25))

        # FORM FRAME (GRID ONLY)
        form = ttk.Frame(main)
        form.pack(fill="x", pady=(0, 20))
        form.grid_columnconfigure(1, weight=1)

        labels = ["Full Name:", "Contact (Email/Phone):", "Username:", "Password:", "Role:"]
        self.entries = {}

        for i, label in enumerate(labels):
            ttk.Label(
                form,
                text=label,
                font=("Segoe UI", 10, "bold")
            ).grid(row=i, column=0, sticky="w", padx=(0, 10), pady=10)

            if label == "Role:":
                if logged_in_user.role == "Manager":
                    role_values = ["Employee"]
                else:
                    role_values = ["Customer", "Employee", "Developer", "Manager", "Owner"]

                entry = ttk.Combobox(form, values=role_values, state="readonly", font=("Segoe UI", 10))
                entry.set(role_values[0])
            else:
                entry = ttk.Entry(
                    form,
                    show="●" if label == "Password:" else "",
                    font=("Segoe UI", 10),
                    width=25
                )

            entry.grid(row=i, column=1, sticky="ew", pady=10, ipady=5)
            self.entries[label] = entry

        # BUTTONS (PACK, full-width)
        btns = ttk.Frame(main)
        btns.pack(pady=(10, 0), fill="x")

        save_btn = ttk.Button(
            btns,
            text="💾 Save User",
            command=self.save_user,
            bootstyle="success",
            width=20
        )
        save_btn.pack(side="left", expand=True, fill="x", padx=(0, 10), ipady=10)

        cancel_btn = ttk.Button(
            btns,
            text="Cancel",
            command=self.destroy,
            bootstyle="secondary-outline",
            width=20
        )
        cancel_btn.pack(side="right", expand=True, fill="x", padx=(10, 0), ipady=10)

    def save_user(self):
        name = self.entries["Full Name:"].get()
        contact = self.entries["Contact (Email/Phone):"].get()
        username = self.entries["Username:"].get()
        password = self.entries["Password:"].get()
        role = self.entries["Role:"].get()

        if not all([name, username, password, role]):
            Messagebox.show_error("Name, Username, Password, and Role are required.", "Error", parent=self)
            return

        if role != "Customer" and not contact:
            contact = "N/A"

        if db.add_user(name, contact, username, password, role, "N/A"):
            Messagebox.show_info(f"{role} '{name}' added successfully.", "Success", parent=self)
            self.parent.load_users()
            self.destroy()
        else:
            Messagebox.show_error("Failed to add user. Username may already exist.", "Error", parent=self)

# helper to refresh users list (auto-added by fixer)
def _auto_refresh_users(ui):
    try:
        users = db.get_all_users()
        if hasattr(ui, 'load_users'):
            ui.load_users()
    except:
        pass
