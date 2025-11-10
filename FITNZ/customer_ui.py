# File: FITNZ/customer_ui.py
import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from . import database as db
from datetime import date, timedelta

class CartPage(bs.Toplevel):
    def __init__(self, parent, cart, customer):
        super().__init__(parent)
        self.parent = parent # This is MainAppPage
        self.cart = cart
        self.customer = customer
        
        self.title("My Shopping Cart")
        self.geometry("600x600")

        self.points_to_redeem = 0
        self.student_discount_applied = False

        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        main_frame = ttk.Frame(self, padding=20); main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1); main_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(main_frame, text="My Cart", font=("Helvetica", 16, "bold"), bootstyle="primary").grid(row=0, column=0, sticky="w", pady=(0, 10))

        cart_frame = ttk.Frame(main_frame); cart_frame.grid(row=1, column=0, sticky="nsew")
        cart_frame.grid_rowconfigure(0, weight=1); cart_frame.grid_columnconfigure(0, weight=1)
        cols = ("name", "price"); self.cart_tree = ttk.Treeview(cart_frame, columns=cols, show="headings", bootstyle="primary")
        self.cart_tree.heading("name", text="Product Name"); self.cart_tree.heading("price", text="Price")
        self.cart_tree.grid(row=0, column=0, sticky="nsew")
        
        ttk.Button(cart_frame, text="Remove Selected", command=self.remove_item, bootstyle="danger-outline").grid(row=1, column=0, sticky="w", pady=(5,0))
        
        summary_frame = ttk.Labelframe(main_frame, text="Order Summary", padding=15, bootstyle="info"); summary_frame.grid(row=2, column=0, sticky="ew", pady=10)
        summary_frame.grid_columnconfigure(1, weight=1)

        self.subtotal_label = ttk.Label(summary_frame, text="Subtotal: $0.00"); self.subtotal_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        self.discount_label = ttk.Label(summary_frame, text="Discount: $0.00"); self.discount_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        self.total_label = ttk.Label(summary_frame, text="Total: $0.00", font=("Helvetica", 12, "bold")); self.total_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        self.points_entry = ttk.Entry(summary_frame); self.points_entry.grid(row=3, column=0, sticky="ew", pady=(10,0))
        self.points_entry.insert(0, "0")
        ttk.Button(summary_frame, text=f"Redeem Points (Max: {customer.loyalty_points})", command=self.apply_points, bootstyle="info-outline").grid(row=3, column=1, sticky="ew", padx=(5,0), pady=(10,0))
        
        if self.customer.membership_level != "Student":
            ttk.Button(summary_frame, text="Apply Student Discount (20%)", command=self.apply_student_discount, bootstyle="warning-outline").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5,0))
        
        ttk.Button(main_frame, text="Proceed to Checkout", command=self.open_checkout, bootstyle="success").grid(row=3, column=0, sticky="ew", ipady=5)

        self.populate_cart()

    def populate_cart(self):
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        for item in self.cart:
            self.cart_tree.insert("", "end", iid=item.product_id, values=(item.name, f"${item.price:.2f}"))
        self.update_summary()

    def remove_item(self):
        selected = self.cart_tree.focus()
        if not selected: return
        self.cart = [item for item in self.cart if item.product_id != selected]
        self.populate_cart()
        self.parent.cart = self.cart # Update the main app's cart

    def update_summary(self):
        subtotal = sum(item.price for item in self.cart)
        
        discount_rate = 0.0
        if self.student_discount_applied:
            discount_rate = 0.20 # 20%
        else:
            discount_rate = self.customer.get_discount_rate()
            
        discount_amount = subtotal * discount_rate
        
        points_discount = self.points_to_redeem * 0.10 # 1 point = 10 cents
        total_discount = discount_amount + points_discount
        
        self.total = subtotal - total_discount
        
        self.subtotal_label.config(text=f"Subtotal: ${subtotal:.2f}")
        self.discount_label.config(text=f"Discount: -${total_discount:.2f}")
        self.total_label.config(text=f"Total: ${self.total:.2f}")

    def apply_points(self):
        try:
            points = int(self.points_entry.get())
            if 0 <= points <= self.customer.loyalty_points:
                self.points_to_redeem = points
                self.update_summary()
                Messagebox.show_info(f"{points} points applied.", "Points Redeemed", parent=self)
            else:
                Messagebox.show_error(f"Please enter a number between 0 and {self.customer.loyalty_points}.", "Invalid Points", parent=self)
        except ValueError:
            Messagebox.show_error("Please enter a valid number.", "Invalid Input", parent=self)

    def apply_student_discount(self):
        if Messagebox.yesno("Are you sure you want to apply a 20% Student Discount? This will override your current membership discount for this sale.", "Confirm Student Discount", parent=self):
            self.student_discount_applied = True
            self.update_summary()

    def open_checkout(self):
        if not self.cart:
            Messagebox.show_error("Your cart is empty.", "Error", parent=self)
            return
        self.withdraw()
        checkout_win = CheckoutPage(self, self.cart, self.customer, self.points_to_redeem, self.total, self.student_discount_applied)
        checkout_win.grab_set()

class CheckoutPage(bs.Toplevel):
    def __init__(self, parent, cart, customer, points_redeemed, total, student_discount_applied):
        super().__init__(parent)
        self.parent = parent.parent # This is MainAppPage
        self.cart_page = parent     # This is CartPage
        self.cart = cart
        self.customer = customer
        self.points_redeemed = points_redeemed
        self.total = total
        self.student_discount_applied = student_discount_applied
        
        self.title("Checkout")
        self.geometry("400x350")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.bind('<Return>', lambda event: self.process_payment())

        # --- THIS IS THE FIX ---
        
        # 1. Title (at the top)
        ttk.Label(self, text="Simulated Payment", font=("Helvetica", 16, "bold"), bootstyle="primary").pack(pady=10, side="top")
        
        # 2. Button Container (at the bottom)
        button_container = ttk.Frame(self, padding=20)
        button_container.pack(side="bottom", fill="x", pady=(0, 10)) # STICK TO BOTTOM
        button_container.grid_columnconfigure((0, 1), weight=1)
        ttk.Button(button_container, text=f"Pay Now ${self.total:.2f}", command=self.process_payment, bootstyle="success-lg").grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=5)
        ttk.Button(button_container, text="Cancel", command=self.on_close, bootstyle="secondary-outline").grid(row=0, column=1, sticky="ew", padx=(5, 0), ipady=5)

        # 3. Form (fills the remaining space in the middle)
        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(expand=True, fill="x", side="top") # FILLS THE REST
        
        # --- End of Fix ---

        ttk.Label(form_frame, text="Card Number:").pack(anchor="w")
        ttk.Entry(form_frame).pack(fill="x", pady=5, ipady=3)
        ttk.Label(form_frame, text="Expiry (MM/YY):").pack(anchor="w")
        ttk.Entry(form_frame).pack(fill="x", pady=5, ipady=3)
        ttk.Label(form_frame, text="CVV:").pack(anchor="w")
        ttk.Entry(form_frame).pack(fill="x", pady=5, ipady=3)

    def process_payment(self):
        delivery_date = date.today() + timedelta(days=5)
        db.process_sale(self.customer, self.cart, self.points_redeemed, self.student_discount_applied, delivery_date)
        Messagebox.show_info(f"Your order has been placed!\nEstimated Delivery: {delivery_date.strftime('%A, %B %d, %Y')}", "Payment Successful", parent=self.parent)
        
        self.parent.clear_cart() 
        
        self.cart_page.destroy()
        self.destroy()
    
    def on_close(self):
        self.cart_page.deiconify() # Show the cart window again
        self.destroy()

class MembershipPage(bs.Toplevel):
    def __init__(self, parent, customer):
        super().__init__(parent)
        self.parent = parent
        self.customer = customer
        self.title("Manage Membership")
        self.geometry("400x400")
        
        frame = ttk.Frame(self, padding=20); frame.pack(expand=True, fill="both")
        
        ttk.Label(frame, text="Upgrade Membership", font=("Helvetica", 16, "bold"), bootstyle="primary").pack(pady=10)
        
        current_level = self.customer.membership_level
        ttk.Label(frame, text=f"Current Level: {current_level}", font=("Helvetica", 12)).pack(pady=5)
        
        ttk.Label(frame, text="Select new level:").pack(pady=(10, 5))
        
        levels = ["Bronze (5%)", "Silver (10%)", "Gold (15%)"]
        self.level_var = tk.StringVar()
        self.level_combo = ttk.Combobox(frame, textvariable=self.level_var, values=levels, state="readonly")
        self.level_combo.pack(fill="x", pady=5, ipady=5)
        
        # --- FIX #1: Changed 'pady=1D40C' to 'pady=10' ---
        ttk.Button(frame, text="Upgrade Membership", command=self.upgrade_membership, bootstyle="success").pack(fill="x", ipady=5, pady=10)
        
        ttk.Separator(frame).pack(fill="x", pady=15)
        
        ttk.Label(frame, text="Are you a student?").pack(pady=5)
        
        student_btn_text = "Already Applied" if current_level == "Student" else "Get Student Discount (20%)"
        self.student_btn = ttk.Button(frame, text=student_btn_text, command=self.upgrade_to_student, bootstyle="info")
        self.student_btn.pack(fill="x", ipady=5)
        if current_level == "Student":
            self.student_btn.config(state="disabled")

    def upgrade_membership(self):
        new_level_str = self.level_var.get()
        if not new_level_str:
            Messagebox.show_error("Please select a level.", "Error", parent=self)
            return
        
        new_level = new_level_str.split(" ")[0] # "Bronze (5%)" -> "Bronze"
        
        if db.update_customer_membership(self.customer._customer_id, new_level):
            Messagebox.show_info(f"Membership upgraded to {new_level}!", "Success", parent=self)
            self.parent.update_customer_info() # Update the main app UI
            self.destroy()
        else:
            Messagebox.show_error("Failed to upgrade membership.", "Error", parent=self)

    def upgrade_to_student(self):
        if db.upgrade_to_student_membership(self.customer._customer_id):
            Messagebox.show_info("Student membership (20% discount) applied!", "Success", parent=self)
            self.parent.update_customer_info() # Update the main app UI
            self.destroy()
        else:
            # --- FIX #2: Changed 'in.py' to 'parent=self' ---
            Messagebox.show_error("Failed to apply student membership.", "Error", parent=self)