# File: FITNZ/customer_ui.py
import random
import tkinter as tk
from datetime import date, timedelta
import ttkbootstrap as bs
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

# Import your database module
from . import database_mysql as db

# ===============================================
# Code Owner: Om (US: Add to cart, View cart, Subtotal)
# ===============================================

class CartPage(bs.Toplevel):
    """Enhanced cart with improved checkout flow"""
    
    def __init__(self, parent, cart: list, customer):
        super().__init__(parent)
        self.parent = parent
        self.cart = list(cart)
        self.customer = customer

        # State
        self.points_to_redeem = 0
        self.student_discount_applied = False
        self.total = 0.0
        self.subtotal = 0.0

        # Window setup
        self.title("🛒 Shopping Cart - Fit NZ")
        self.geometry("800x700")
        self.resizable(True, True)
        self.transient(parent)

        # Layout root
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ttk.Frame(self, padding=20)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        header = ttk.Label(
            header_frame, 
            text="🛒 Your Shopping Cart", 
            font=("Segoe UI", 20, "bold"), 
            bootstyle="primary"
        )
        header.pack(side="left")

        # Cart items frame
        cart_frame = ttk.Labelframe(
            main_frame, 
            text="Cart Items", 
            padding=15,
            bootstyle="info"
        )
        cart_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        cart_frame.grid_rowconfigure(0, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)

        # Treeview frame
        tree_frame = ttk.Frame(cart_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("name", "price", "quantity", "total")
        self.cart_tree = ttk.Treeview(
            tree_frame, 
            columns=cols, 
            show="headings", 
            bootstyle="primary",
            selectmode="browse"
        )
        
        self.cart_tree.heading("name", text="Product Name", anchor="w")
        self.cart_tree.heading("price", text="Unit Price", anchor="e")
        self.cart_tree.heading("quantity", text="Qty", anchor="center")
        self.cart_tree.heading("total", text="Total", anchor="e")
        
        self.cart_tree.column("name", width=300, anchor="w")
        self.cart_tree.column("price", width=100, anchor="e")
        self.cart_tree.column("quantity", width=80, anchor="center")
        self.cart_tree.column("total", width=100, anchor="e")
        
        self.cart_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        vsb = ttk.Scrollbar(
            tree_frame, 
            orient="vertical", 
            command=self.cart_tree.yview,
            bootstyle="secondary-round"
        )
        vsb.grid(row=0, column=1, sticky="ns")
        self.cart_tree.configure(yscrollcommand=vsb.set)

        # Cart actions
        actions_frame = ttk.Frame(cart_frame)
        actions_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        
        ttk.Button(
            actions_frame, 
            text="🗑️ Remove Selected", 
            command=self.remove_item, 
            bootstyle="danger-outline",
            width=18
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            actions_frame, 
            text="🔄 Update Quantities", 
            command=self.update_quantities, 
            bootstyle="warning-outline",
            width=18
        ).pack(side="left")

        # Summary frame
        summary_frame = ttk.Labelframe(
            main_frame, 
            text="💰 Order Summary", 
            padding=18, 
            bootstyle="success"
        )
        summary_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        summary_frame.grid_columnconfigure(1, weight=1)

        # Summary labels
        ttk.Label(summary_frame, text="Subtotal:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", pady=4)
        self.subtotal_label = ttk.Label(summary_frame, text="$0.00", font=("Segoe UI", 11), bootstyle="primary")
        self.subtotal_label.grid(row=0, column=1, sticky="e", pady=4)
        
        ttk.Label(summary_frame, text="Discount:", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w", pady=4)
        self.discount_label = ttk.Label(summary_frame, text="$0.00", font=("Segoe UI", 11), bootstyle="success")
        self.discount_label.grid(row=1, column=1, sticky="e", pady=4)
        
        ttk.Separator(summary_frame, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)
        
        ttk.Label(summary_frame, text="Total:", font=("Segoe UI", 14, "bold")).grid(row=3, column=0, sticky="w", pady=4)
        self.total_label = ttk.Label(summary_frame, text="$0.00", font=("Segoe UI", 14, "bold"), bootstyle="primary")
        self.total_label.grid(row=3, column=1, sticky="e", pady=4)

        # Discounts and points frame
        discounts_frame = ttk.Frame(main_frame)
        discounts_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        discounts_frame.grid_columnconfigure(0, weight=1)
        discounts_frame.grid_columnconfigure(1, weight=1)

        # Points redemption
        points_frame = ttk.Labelframe(
            discounts_frame, 
            text="🎁 Redeem Loyalty Points", 
            padding=12,
            bootstyle="info"
        )
        points_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        points_container = ttk.Frame(points_frame)
        points_container.pack(fill="x")
        points_container.grid_columnconfigure(0, weight=1)

        self.points_entry = ttk.Entry(points_container, font=("Segoe UI", 10), width=10)
        self.points_entry.grid(row=0, column=0, sticky="ew", ipady=5, padx=(0, 10))
        self.points_entry.insert(0, "0")

        max_points = getattr(self.customer, "loyalty_points", 0)
        redeem_btn = ttk.Button(
            points_container, 
            text=f"Apply (Max: {max_points})", 
            command=self.apply_points, 
            bootstyle="info-outline",
            width=18
        )
        redeem_btn.grid(row=0, column=1, sticky="ew")

        # Student discount
        student_frame = ttk.Labelframe(
            discounts_frame, 
            text="🎓 Student Discount", 
            padding=12,
            bootstyle="warning"
        )
        student_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        if getattr(self.customer, "membership_level", "") != "Student":
            ttk.Button(
                student_frame, 
                text="Apply 20% Discount", 
                command=self.apply_student_discount, 
                bootstyle="warning-outline",
                width=20
            ).pack(fill="x", ipady=6)
        else:
            ttk.Label(
                student_frame,
                text="Student discount applied!",
                bootstyle="success",
                font=("Segoe UI", 10, "bold")
            ).pack(pady=5)

        # Checkout button - MAKE SURE IT'S VISIBLE
        checkout_btn = ttk.Button(
            main_frame, 
            text="🚀 Proceed to Checkout", 
            command=self.open_checkout, 
            bootstyle="success",
            width=30
        )
        checkout_btn.grid(row=4, column=0, sticky="ew", ipady=12, pady=(10, 0))  # Added pady for spacing

        # Populate cart
        self.populate_cart()

    def populate_cart(self):
        """Fill the treeview with current cart contents and update summary."""
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        
        # Group items by product_id to handle quantities
        cart_items = {}
        for item in self.cart:
            product_id = getattr(item, "product_id", id(item))
            if product_id not in cart_items:
                cart_items[product_id] = {
                    'item': item,
                    'quantity': 1,
                    'total': float(getattr(item, 'price', 0.0))
                }
            else:
                cart_items[product_id]['quantity'] += 1
                cart_items[product_id]['total'] += float(getattr(item, 'price', 0.0))
        
        for product_id, cart_item in cart_items.items():
            item = cart_item['item']
            quantity = cart_item['quantity']
            total_price = cart_item['total']
            
            iid = str(product_id)
            price_display = f"${float(getattr(item, 'price', 0.0)):.2f}"
            total_display = f"${total_price:.2f}"
            name = getattr(item, "name", "<Unnamed>")
            
            self.cart_tree.insert("", "end", iid=iid, 
                                values=(name, price_display, quantity, total_display))
        
        self.update_summary()
