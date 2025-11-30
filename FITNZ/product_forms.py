# File: FITNZ/product_forms.py

import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from . import database_mysql as db

# ============================================
# Code Owner: Umang (US: Manage entire product inventory - Add/Edit Products)
# This entire file is owned by Umang's US.
# ============================================

class AddProductPage(bs.Toplevel):
    def __init__(self, parent, user):
        super().__init__(parent)

        self.parent = parent
        self.title("➕ Add Product")
        self.geometry("420x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        main = ttk.Frame(self, padding=25)
        main.pack(expand=True, fill="both")

        ttk.Label(
            main,
            text="➕ Add New Product",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).pack(pady=(0, 20))

        # FORM CONTAINER (GRID)
        form = ttk.Frame(main)
        form.pack(fill="x")
        form.grid_columnconfigure(1, weight=1)

        labels = ["Name:", "Price:", "Stock:"]
        self.entries = {}

        for i, label in enumerate(labels):
            ttk.Label(
                form,
                text=label,
                font=("Segoe UI", 10, "bold")
            ).grid(row=i, column=0, sticky="w", pady=10)

            entry = ttk.Entry(form, font=("Segoe UI", 10))
            entry.grid(row=i, column=1, sticky="ew", ipady=4, padx=(10, 0))
            self.entries[label] = entry

        # Buttons
        btns = ttk.Frame(main)
        btns.pack(pady=(25, 0), fill="x")

        ttk.Button(
            btns,
            text="💾 Save Product",
            bootstyle="success",
            width=18,
            command=self.save_product
        ).pack(side="left", expand=True, padx=10, ipady=6)

        ttk.Button(
            btns,
            text="Cancel",
            bootstyle="secondary-outline",
            width=18,
            command=self.destroy
        ).pack(side="right", expand=True, padx=10, ipady=6)

    def save_product(self):
        name = self.entries["Name:"].get()
        price = self.entries["Price:"].get()
        stock = self.entries["Stock:"].get()

        if not name or not price or not stock:
            Messagebox.show_error("All fields are required.", "Error", parent=self)
            return

        try:
            price = float(price)
            stock = int(stock)
        except:
            Messagebox.show_error("Price must be number & stock must be integer.", "Invalid Input", parent=self)
            return

        if db.add_product(name, price, stock):
            Messagebox.show_info("Product added successfully!", "Success", parent=self)
            self.parent.load_products()
            self.destroy()
        else:
            Messagebox.show_error("Failed to add product.", "Error", parent=self)



# ============================================
#   Edit Product Page
# ============================================

class EditProductPage(bs.Toplevel):
    """Window to edit an existing product"""

    def __init__(self, parent, product_id):
        super().__init__(parent)

        self.parent = parent
        self.product_id = product_id
        self.title("✏️ Edit Product - Fit NZ")
        self.geometry("450x420")
        self.resizable(False, False)
        self.transient(parent)

        # Fetch product
        self.product = db.get_product_by_id(product_id)
        if not self.product:
            Messagebox.show_error("Product not found!", "Error", parent=self)
            self.destroy()
            return

        frame = ttk.Frame(self, padding=25)
        frame.pack(expand=True, fill="both")

        ttk.Label(
            frame,
            text="✏️ Edit Product",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).pack(pady=(0, 20))

        # Labels and entries
        labels = ["Product Name:", "Price:", "Stock:"]
        self.entries = {}

        # PRODUCT NAME
        ttk.Label(frame, text="Product Name:", font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=10)
        self.name_entry = ttk.Entry(frame, font=("Segoe UI", 10), width=25)
        self.name_entry.grid(row=1, column=1, sticky="ew", pady=10, ipady=6)
        self.name_entry.insert(0, self.product.name)

        # PRICE
        ttk.Label(frame, text="Price:", font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=10)
        self.price_entry = ttk.Entry(frame, font=("Segoe UI", 10), width=25)
        self.price_entry.grid(row=2, column=1, sticky="ew", pady=10, ipady=6)
        self.price_entry.insert(0, str(self.product.price))

        # STOCK
        ttk.Label(frame, text="Stock:", font=("Segoe UI", 10, "bold")).grid(
            row=3, column=0, sticky="w", padx=(0, 10), pady=10)
        self.stock_entry = ttk.Entry(frame, font=("Segoe UI", 10), width=25)
        self.stock_entry.grid(row=3, column=1, sticky="ew", pady=10, ipady=6)
        self.stock_entry.insert(0, str(self.product.stock))

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(25, 0))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ttk.Button(
            btn_frame,
            text="💾 Save Changes",
            bootstyle="success",
            command=self.save_changes,
            width=20
        ).grid(row=0, column=0, padx=5, ipady=8)

        ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="secondary-outline",
            command=self.destroy,
            width=20
        ).grid(row=0, column=1, padx=5, ipady=8)

    def save_changes(self):
        """Save edited product information"""
        name = self.name_entry.get().strip()
        price = self.price_entry.get().strip()
        stock = self.stock_entry.get().strip()

        if not name or not price or not stock:
            Messagebox.show_error("All fields are required.", "Missing Data", parent=self)
            return

        try:
            price = float(price)
            stock = int(stock)
        except:
            Messagebox.show_error("Enter valid numeric values for price and stock.", "Invalid Input", parent=self)
            return

        # Update product in database
        updated = db.update_product(
            self.product_id,
            name,
            price,
            stock
        )

        if updated:
            Messagebox.show_info("Product updated successfully.", "Success", parent=self)
            self.parent.load_products()
            self.destroy()
        else:
            Messagebox.show_error("Failed to update product.", "Error", parent=self)


