# File: FITNZ/admin_ui.py
import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from . import database as db # <-- THIS LINE IS NOW CORRECTED

class AdminPage(bs.Toplevel):
    def __init__(self, parent, logged_in_user):
        super().__init__(parent)
        self.logged_in_user = logged_in_user
        self.title("Admin Panel - User Management")
        self.minsize(600, 500)

        header_frame = ttk.Frame(self, padding=10, bootstyle="secondary")
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="User Management", font=("Helvetica", 16, "bold"), bootstyle="inverse-secondary").pack(side="left")

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        tree_frame = ttk.Labelframe(main_frame, text="All Users", padding=10, bootstyle="info")
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("ID", "Username", "Role", "Name")
        self.user_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", bootstyle="primary")
        for col in cols: self.user_tree.heading(col, text=col)
        self.user_tree.column("ID", width=40, stretch=False)
        self.user_tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.user_tree.yview, bootstyle="secondary-round")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        self.load_users()

        action_frame = ttk.Frame(tree_frame)
        action_frame.grid(row=0, column=2, sticky="ns", padx=(10, 0))
        ttk.Button(action_frame, text="Add User", command=self.open_add_user, bootstyle="success-outline").pack(pady=5, fill="x")
        ttk.Button(action_frame, text="Delete User", command=self.delete_user, bootstyle="danger").pack(pady=5, fill="x")
        
        ttk.Button(main_frame, text="Back", command=self.destroy, bootstyle="secondary").grid(row=1, column=0, pady=(10,0), sticky="e")

    def open_add_user(self):
        add_win = AddUserPage(self, self.logged_in_user)
        add_win.grab_set()

    def load_users(self):
        for i in self.user_tree.get_children(): self.user_tree.delete(i)
        for user in db.get_all_users():
            user_id = getattr(user, 'employee_id', getattr(user, '_customer_id', 'N/A'))
            name = getattr(user, 'name', getattr(user, '_name', 'N/A'))
            self.user_tree.insert("", "end", iid=user_id, values=(user_id, user.username, user.role, name))

    def delete_user(self):
        selected_item_id = self.user_tree.focus()
        if not selected_item_id: Messagebox.show_warning("Please select a user to delete.", "No Selection", parent=self); return
        if selected_item_id == "E001": Messagebox.show_error("Cannot delete the primary developer account.", "Error", parent=self); return
        if Messagebox.yesno(f"Are you sure you want to delete user ID {selected_item_id}?", "Confirm Deletion", parent=self):
            if db.delete_user_by_id(selected_item_id):
                Messagebox.show_info("User deleted successfully.", "Success", parent=self); self.load_users()
            else: Messagebox.show_error("Failed to delete user.", "Error", parent=self)

class AddUserPage(bs.Toplevel):
    def __init__(self, parent, logged_in_user):
        super().__init__(parent); self.parent = parent
        self.title("Add New User"); self.geometry("350x300"); self.resizable(False, False)
        frame = ttk.Frame(self, padding=20); frame.pack(expand=True, fill="both")
        
        labels = ["Full Name:", "Contact (Email/Phone):", "Username:", "Password:", "Role:"]
        self.entries = {}
        for i, label in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            if label == "Role:":
                if logged_in_user.role == "Manager":
                    role_values = ["Employee"]
                else:
                    role_values = ["Customer", "Employee", "Developer", "Manager", "Owner"]
                
                self.entries[label] = ttk.Combobox(frame, values=role_values, state="readonly")
                self.entries[label].set(role_values[0])
            else:
                self.entries[label] = ttk.Entry(frame, show="*" if label == "Password:" else "")
            self.entries[label].grid(row=i, column=1, sticky="ew")
        
        frame.grid_columnconfigure(1, weight=1)
        ttk.Button(frame, text="Save User", command=self.save_user, bootstyle="success").grid(row=len(labels), column=0, columnspan=2, pady=20, ipady=5)

    def save_user(self):
        name = self.entries["Full Name:"].get(); contact = self.entries["Contact (Email/Phone):"].get(); username = self.entries["Username:"].get(); password = self.entries["Password:"].get(); role = self.entries["Role:"].get()
        if not all([name, username, password, role]): Messagebox.show_error("Name, Username, Password, and Role are required.", "Error", parent=self); return
        if role != "Customer" and not contact: contact = "N/A"
        if db.add_user(name, contact, username, password, role, "N/A"): #Adds N/A for staff address
            Messagebox.show_info(f"{role} '{name}' added successfully.", "Success", parent=self); self.parent.load_users(); self.destroy()
        else: Messagebox.show_error("Failed to add user. Username may already exist.", "Error", parent=self)