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



# ===============================================
# Code Owner: Rajina (US: Calculate/Apply Discounts - Membership/Student/Points)
# ===============================================


    def update_summary(self):
        """Recalculate subtotal, discounts and total, update labels."""
        self.subtotal = sum(float(getattr(item, "price", 0.0)) for item in self.cart)

        # Calculate discount rate
        if self.student_discount_applied:
            discount_rate = 0.20
        else:
            discount_rate = getattr(self.customer, "get_discount_rate", lambda: 0.0)()
        
        discount_amount = self.subtotal * discount_rate

        # Points conversion: 1 point = $0.10
        points_discount = float(self.points_to_redeem) * 0.10
        total_discount = discount_amount + points_discount

        # Prevent negative totals
        self.total = max(0.0, self.subtotal - total_discount)

        self.subtotal_label.config(text=f"${self.subtotal:.2f}")
        self.discount_label.config(text=f"-${total_discount:.2f}")
        self.total_label.config(text=f"${self.total:.2f}")

    def remove_item(self):
        """Remove selected item from cart and refresh."""
        selected = self.cart_tree.selection()
        if not selected:
            Messagebox.show_warning("Please select an item to remove.", "No Selection", parent=self)
            return
        
        for iid in selected:
            # Find and remove one instance of the product
            product_id = iid
            for i, item in enumerate(self.cart):
                if str(getattr(item, "product_id", id(item))) == str(product_id):
                    self.cart.pop(i)
                    break
        
        # Update parent's cart
        if hasattr(self.parent, "cart"):
            self.parent.cart = list(self.cart)
        
        self.populate_cart()

    def update_quantities(self):
        """Open quantity update dialog"""
        selected = self.cart_tree.selection()
        if not selected:
            Messagebox.show_warning("Please select an item to update quantity.", "No Selection", parent=self)
            return
        
        QuantityUpdatePage(self, self.cart, selected[0])

    def apply_points(self):
        """Apply loyalty points entered by the user."""
        try:
            points = int(self.points_entry.get())
        except ValueError:
            Messagebox.show_error("Please enter a valid number of points.", "Invalid Input", parent=self)
            return

        max_points = int(getattr(self.customer, "loyalty_points", 0))
        if points < 0 or points > max_points:
            Messagebox.show_error(f"Please enter a number between 0 and {max_points}.", "Invalid Points", parent=self)
            return

        self.points_to_redeem = points
        self.update_summary()
        Messagebox.show_info(f"{points} points applied successfully.", "Points Redeemed", parent=self)

    def apply_student_discount(self):
        """Apply student discount."""
        if self.student_discount_applied:
            Messagebox.show_info("Student discount is already applied.", "Info", parent=self)
            return
            
        ok = Messagebox.yesno(
            "Apply 20% Student Discount?\n\nThis will override your current membership discount for this purchase.",
            "Confirm Student Discount",
            parent=self,
        )
        if ok:
            self.student_discount_applied = True
            self.update_summary()
            Messagebox.show_info("20% student discount applied!", "Discount Applied", parent=self)

    def open_checkout(self):
        """Open checkout window."""
        if not self.cart:
            Messagebox.show_error("Your cart is empty.", "Error", parent=self)
            return

        # Validate stock
        for item in self.cart:
            product_id = getattr(item, "product_id", "")
            product = db.get_product_by_id(product_id)
            if product and product.stock <= 0:
                Messagebox.show_error(
                    f"Sorry, {product.name} is out of stock. Please remove it from your cart.",
                    "Out of Stock",
                    parent=self
                )
                return

        # 🔥 FIX: employees must calculate total manually  
        total_amount = sum(getattr(item, "price", 0) for item in self.cart)

        self.withdraw()

        checkout_win = CheckoutPage(
            parent=self,
            cart=self.cart,
            customer=self.customer,
            points_redeemed=self.points_to_redeem,
            total=total_amount,
            student_discount_applied=self.student_discount_applied
        )

        checkout_win.grab_set()


class QuantityUpdatePage(bs.Toplevel):
    """Dialog for updating item quantities"""
    
    def __init__(self, parent, cart, product_id):
        super().__init__(parent)
        self.parent = parent
        self.cart = cart
        self.product_id = product_id
        
        self.title("Update Quantity")
        self.geometry("300x200")
        self.resizable(False, False)
        self.transient(parent)
        
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")
        
        # Count current quantity
        current_qty = sum(1 for item in cart if str(getattr(item, "product_id", id(item))) == str(product_id))
        
        ttk.Label(main_frame, text="Update Quantity:", font=("Segoe UI", 12, "bold")).pack(pady=(0, 15))
        
        qty_frame = ttk.Frame(main_frame)
        qty_frame.pack(pady=10)
        
        ttk.Label(qty_frame, text="Quantity:").pack(side="left", padx=(0, 10))
        
        self.qty_var = tk.StringVar(value=str(current_qty))
        qty_spinbox = ttk.Spinbox(
            qty_frame, 
            from_=1, 
            to=100, 
            textvariable=self.qty_var,
            width=10,
            font=("Segoe UI", 11)
        )
        qty_spinbox.pack(side="left")
        
        # Buttons - MAKE VISIBLE
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))
        
        ttk.Button(
            btn_frame,
            text="Update",
            command=self.update_quantity,
            bootstyle="success",
            width=15
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bootstyle="secondary",
            width=15
        ).pack(side="right")

    def update_quantity(self):
        try:
            new_qty = int(self.qty_var.get())
            if new_qty < 1:
                Messagebox.show_error("Quantity must be at least 1.", "Invalid Quantity", parent=self)
                return
        except ValueError:
            Messagebox.show_error("Please enter a valid number.", "Invalid Input", parent=self)
            return
        
        # Update cart
        product_items = [item for item in self.cart if str(getattr(item, "product_id", id(item))) == str(self.product_id)]
        
        # Remove all instances
        for item in product_items:
            self.cart.remove(item)
        
        # Add new quantity
        if product_items:
            sample_item = product_items[0]
            for _ in range(new_qty):
                self.cart.append(sample_item)
        
        # Refresh parent
        self.parent.populate_cart()
        self.destroy()


