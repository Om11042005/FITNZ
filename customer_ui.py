import tkinter as tk
from datetime import date, timedelta
import ttkbootstrap as bs
from ttkbootstrap import ttk
from ttkbootstrap.dialogs import Messagebox

# Import your database module (adjust relative import if necessary)
from . import database as db


class CartPage(bs.Toplevel):
    """Top-level window that displays current cart, allows removing items,
    redeeming points and applying discounts, and proceeds to checkout.
    """

    def __init__(self, parent, cart: list, customer):
        """
        parent: main app window (MainAppPage)
        cart: list of product-like objects with attributes: product_id, name, price
        customer: Customer instance
        """
        super().__init__(parent)
        self.parent = parent
        self.cart = list(cart)
        self.customer = customer

        # State
        self.points_to_redeem = 0
        self.student_discount_applied = False
        self.total = 0.0

        # Window setup
        self.title("🛒 My Shopping Cart - Fit NZ")
        self.geometry("720x680")
        self.resizable(True, True)
        self.transient(parent)

        # Layout root
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ttk.Frame(self, padding=20)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Header with improved styling
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        header = ttk.Label(
            header_frame, 
            text="🛒 My Shopping Cart", 
            font=("Segoe UI", 20, "bold"), 
            bootstyle="primary"
        )
        header.pack(side="left")

        # Cart area with improved styling
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

        cols = ("name", "price")
        self.cart_tree = ttk.Treeview(
            tree_frame, 
            columns=cols, 
            show="headings", 
            bootstyle="primary",
            selectmode="browse"
        )
        self.cart_tree.heading("name", text="Product Name", anchor="w")
        self.cart_tree.heading("price", text="Price", anchor="e")
        self.cart_tree.column("name", width=450, anchor="w")
        self.cart_tree.column("price", width=150, anchor="e")
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

        # Remove button
        buttons_row = ttk.Frame(cart_frame)
        buttons_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        
        ttk.Button(
            buttons_row, 
            text="🗑️ Remove Selected", 
            command=self.remove_item, 
            bootstyle="danger-outline",
            width=18
        ).pack(side="left")

        # Summary frame with improved styling
        summary_frame = ttk.Labelframe(
            main_frame, 
            text="💰 Order Summary", 
            padding=18, 
            bootstyle="success"
        )
        summary_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        summary_frame.grid_columnconfigure(0, weight=1)

        # Summary labels with better formatting
        self.subtotal_label = ttk.Label(
            summary_frame, 
            text="Subtotal: $0.00",
            font=("Segoe UI", 11)
        )
        self.subtotal_label.grid(row=0, column=0, sticky="w", pady=4)
        
        self.discount_label = ttk.Label(
            summary_frame, 
            text="Discount: $0.00",
            font=("Segoe UI", 11),
            bootstyle="success"
        )
        self.discount_label.grid(row=1, column=0, sticky="w", pady=4)
        
        ttk.Separator(summary_frame, orient="horizontal").grid(row=2, column=0, sticky="ew", pady=8)
        
        self.total_label = ttk.Label(
            summary_frame, 
            text="Total: $0.00", 
            font=("Segoe UI", 14, "bold"),
            bootstyle="primary"
        )
        self.total_label.grid(row=3, column=0, sticky="w", pady=(4, 12))

        # Points redemption section
        points_label_frame = ttk.Labelframe(
            summary_frame, 
            text="🎁 Redeem Loyalty Points", 
            padding=12,
            bootstyle="info"
        )
        points_label_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        points_label_frame.grid_columnconfigure(0, weight=1)
        
        points_container = ttk.Frame(points_label_frame)
        points_container.grid(row=0, column=0, sticky="ew")
        points_container.grid_columnconfigure(0, weight=1)

        self.points_entry = ttk.Entry(
            points_container, 
            font=("Segoe UI", 10),
            width=10
        )
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

        # Student discount button
        if getattr(self.customer, "membership_level", "") != "Student":
            ttk.Button(
                summary_frame, 
                text="🎓 Apply Student Discount (20%)", 
                command=self.apply_student_discount, 
                bootstyle="warning-outline",
                width=30
            ).grid(row=5, column=0, sticky="ew", pady=(5, 0))

        # Proceed to checkout button
        checkout_btn = ttk.Button(
            main_frame, 
            text="💳 Proceed to Checkout", 
            command=self.open_checkout, 
            bootstyle="success",
            width=30
        )
        checkout_btn.grid(row=3, column=0, sticky="ew", ipady=10)

        # Populate
        self.populate_cart()

    def populate_cart(self):
        """Fill the treeview with current cart contents and update summary."""
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        for item in self.cart:
            # item's product_id should be unique and string-like (convert if necessary)
            iid = str(getattr(item, "product_id", id(item)))
            price_display = f"${float(getattr(item, 'price', 0.0)):.2f}"
            name = getattr(item, "name", "<Unnamed>")
            self.cart_tree.insert("", "end", iid=iid, values=(name, price_display))
        self.update_summary()

    def remove_item(self):
        """Remove selected item from cart and refresh."""
        selected = self.cart_tree.selection()
        if not selected:
            Messagebox.show_warning("Please select an item to remove.", "No Selection", parent=self)
            return
        # selection can be multiple; remove all
        for iid in selected:
            # remove matching product(s) by id
            self.cart = [item for item in self.cart if str(getattr(item, "product_id", id(item))) != str(iid)]
        # Update parent's cart if it exists
        if hasattr(self.parent, "cart"):
            self.parent.cart = list(self.cart)
        self.populate_cart()

    def update_summary(self):
        """Recalculate subtotal, discounts and total, update labels."""
        subtotal = sum(float(getattr(item, "price", 0.0)) for item in self.cart)

        # Decide discount rate
        if self.student_discount_applied:
            discount_rate = 0.20
        else:
            # fall back to customer.get_discount_rate() if present
            discount_rate = 0.0
            getter = getattr(self.customer, "get_discount_rate", None)
            if callable(getter):
                try:
                    discount_rate = float(getter())
                except Exception:
                    discount_rate = 0.0

        discount_amount = subtotal * discount_rate

        # Points conversion: 1 point = $0.10
        points_discount = float(self.points_to_redeem) * 0.10
        total_discount = discount_amount + points_discount

        # Prevent negative totals
        total = max(0.0, subtotal - total_discount)

        self.total = total
        self.subtotal_label.config(text=f"Subtotal: ${subtotal:.2f}")
        self.discount_label.config(text=f"Discount: -${total_discount:.2f}")
        self.total_label.config(text=f"Total: ${self.total:.2f}")

    def apply_points(self):
        """Apply loyalty points entered by the user."""
        try:
            points = int(self.points_entry.get())
        except Exception:
            Messagebox.show_error("Please enter a valid integer number of points.", "Invalid Input", parent=self)
            return

        max_points = int(getattr(self.customer, "loyalty_points", 0))
        if points < 0 or points > max_points:
            Messagebox.show_error(f"Please enter a number between 0 and {max_points}.", "Invalid Points", parent=self)
            return

        self.points_to_redeem = points
        self.update_summary()
        Messagebox.show_info(f"{points} points applied.", "Points Redeemed", parent=self)

    def apply_student_discount(self):
        """Confirm and apply a temporary student discount for this sale only."""
        ok = Messagebox.yesno(
            "Are you sure you want to apply a 20% Student Discount? "
            "This will override your current membership discount for this sale.",
            "Confirm Student Discount",
            parent=self,
        )
        if ok:
            self.student_discount_applied = True
            self.update_summary()

    def open_checkout(self):
        """Open checkout window (simulated payment)."""
        if not self.cart:
            Messagebox.show_error("Your cart is empty.", "Error", parent=self)
            return
        # Hide this cart window while checkout open
        self.withdraw()
        checkout_win = CheckoutPage(self, self.cart, self.customer, self.points_to_redeem, self.total, self.student_discount_applied)
        # Make checkout modal relative to main app
        checkout_win.grab_set()


class CheckoutPage(bs.Toplevel):
    """Simulated payment dialog - processes sale via db.process_sale()"""

    def __init__(self, parent: CartPage, cart: list, customer, points_redeemed: int, total: float, student_discount_applied: bool):
        """
        parent: instance of CartPage
        cart: list of cart items
        customer: Customer instance
        points_redeemed: integer
        total: float final amount to charge
        """
        super().__init__(parent)
        # parent.parent is the main app (MainAppPage)
        self.cart_page = parent
        self.parent_app = getattr(parent, "parent", None)
        self.cart = list(cart)
        self.customer = customer
        self.points_redeemed = int(points_redeemed or 0)
        self.total = float(total or 0.0)
        self.student_discount_applied = bool(student_discount_applied)

        self.title("💳 Checkout - Fit NZ")
        self.geometry("480x520")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)

        # Bind Enter to process payment
        self.bind('<Return>', lambda event: self.process_payment())

        # Main container
        main_container = ttk.Frame(self, padding=25)
        main_container.pack(expand=True, fill="both")

        # Header
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill="x", pady=(0, 10))
        
        title = ttk.Label(
            title_frame, 
            text="💳 Payment Information", 
            font=("Segoe UI", 18, "bold"), 
            bootstyle="primary"
        )
        title.pack(side="left")
        
        # Amount to pay
        amount_frame = ttk.Labelframe(
            main_container, 
            text="Total Amount", 
            padding=15,
            bootstyle="success"
        )
        amount_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            amount_frame, 
            text=f"${self.total:.2f}", 
            font=("Segoe UI", 24, "bold"),
            bootstyle="primary"
        ).pack()

        # Payment form
        form_frame = ttk.Labelframe(
            main_container, 
            text="Card Details", 
            padding=20,
            bootstyle="info"
        )
        form_frame.pack(expand=True, fill="both")

        # Card number
        ttk.Label(
            form_frame, 
            text="Card Number:", 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        self.card_entry = ttk.Entry(
            form_frame, 
            font=("Segoe UI", 11),
            width=30
        )
        self.card_entry.pack(fill="x", pady=(0, 15), ipady=7)
        self.card_entry.bind('<Return>', lambda e: self.expiry_entry.focus())

        # Expiry
        ttk.Label(
            form_frame, 
            text="Expiry Date (MM/YY):", 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        self.expiry_entry = ttk.Entry(
            form_frame, 
            font=("Segoe UI", 11),
            width=30
        )
        self.expiry_entry.pack(fill="x", pady=(0, 15), ipady=7)
        self.expiry_entry.bind('<Return>', lambda e: self.cvv_entry.focus())

        # CVV
        ttk.Label(
            form_frame, 
            text="CVV:", 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        self.cvv_entry = ttk.Entry(
            form_frame, 
            show="●",
            font=("Segoe UI", 11),
            width=30
        )
        self.cvv_entry.pack(fill="x", pady=(0, 15), ipady=7)
        self.cvv_entry.bind('<Return>', lambda e: self.process_payment())
        
        # Focus on card entry
        self.card_entry.focus_set()

        # Buttons
        button_container = ttk.Frame(main_container)
        button_container.pack(fill="x", pady=(15, 0))
        button_container.grid_columnconfigure((0, 1), weight=1)

        pay_text = f"💳 Pay ${self.total:.2f}"
        ttk.Button(
            button_container, 
            text=pay_text, 
            command=self.process_payment, 
            bootstyle="success",
            width=18
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=10)
        
        ttk.Button(
            button_container, 
            text="Cancel", 
            command=self.on_close, 
            bootstyle="secondary-outline",
            width=18
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0), ipady=10)

    def validate_payment_fields(self) -> bool:
        """Simple validation for card fields (simulated)."""
        card = (self.card_entry.get() or "").strip()
        expiry = (self.expiry_entry.get() or "").strip()
        cvv = (self.cvv_entry.get() or "").strip()

        if not card:
            Messagebox.show_error("Please enter your card number.", "Missing Card Number", parent=self)
            self.card_entry.focus_set()
            return False
        
        if not expiry:
            Messagebox.show_error("Please enter the card expiry date (MM/YY).", "Missing Expiry", parent=self)
            self.expiry_entry.focus_set()
            return False
        
        if not cvv:
            Messagebox.show_error("Please enter the CVV code.", "Missing CVV", parent=self)
            self.cvv_entry.focus_set()
            return False
        
        # Basic format validation (simulated - not secure)
        if len(card) < 13 or len(card) > 19 or not card.isdigit():
            Messagebox.show_error(
                "Card number must be between 13-19 digits and contain only numbers.", 
                "Invalid Card Number", 
                parent=self
            )
            self.card_entry.focus_set()
            return False
        
        if len(cvv) < 3 or len(cvv) > 4 or not cvv.isdigit():
            Messagebox.show_error(
                "CVV must be 3-4 digits and contain only numbers.", 
                "Invalid CVV", 
                parent=self
            )
            self.cvv_entry.focus_set()
            return False
        
        # Validate expiry format (MM/YY)
        if '/' not in expiry or len(expiry) != 5:
            Messagebox.show_error(
                "Expiry date must be in MM/YY format (e.g., 12/25).", 
                "Invalid Expiry Format", 
                parent=self
            )
            self.expiry_entry.focus_set()
            return False
        
        return True

    def process_payment(self):
        """Simulate payment processing, then call db.process_sale and finalize order."""
        # Validate fields (keeps UX sane)
        if not self.validate_payment_fields():
            return

        # Compute delivery date (example: +5 days)
        delivery_date = date.today() + timedelta(days=5)

        try:
            # db.process_sale is expected to record the sale, deduct points, update membership benefits, etc.
            db.process_sale(self.customer, self.cart, self.points_redeemed, self.student_discount_applied, delivery_date)
        except Exception as e:
            # If database step fails, show error and keep checkout open
            Messagebox.show_error(f"Failed to process the sale: {e}", "Database Error", parent=self)
            return

        # Inform the user and update UI
        order_summary = (
            f"✅ Payment Successful!\n\n"
            f"Your order has been placed.\n\n"
            f"Total Amount: ${self.total:.2f}\n"
            f"Estimated Delivery: {delivery_date.strftime('%A, %B %d, %Y')}\n\n"
            f"Thank you for shopping with Fit NZ!"
        )
        Messagebox.show_info(
            order_summary,
            "Order Confirmed",
            parent=self,
        )

        # Clear cart on main app if method exists
        if self.parent_app and hasattr(self.parent_app, "clear_cart") and callable(self.parent_app.clear_cart):
            try:
                self.parent_app.clear_cart()
            except Exception:
                # ignore if clear_cart fails — main app may manage cart differently
                pass

        # Destroy cart page and checkout
        try:
            self.cart_page.destroy()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def on_close(self):
        """Called when user cancels checkout — show cart page again and close checkout."""
        try:
            self.cart_page.deiconify()
        except Exception:
            pass
        self.destroy()


class MembershipPage(bs.Toplevel):
    """Manage membership upgrades on a separate modal window."""

    def __init__(self, parent, customer):
        super().__init__(parent)
        self.parent = parent  # main app
        self.customer = customer

        self.title("⭐ Manage Membership - Fit NZ")
        self.geometry("480x550")
        self.resizable(False, False)
        self.transient(parent)

        # Main container
        frame = ttk.Frame(self, padding=25)
        frame.pack(expand=True, fill="both")

        # Header
        ttk.Label(
            frame, 
            text="⭐ Upgrade Your Membership", 
            font=("Segoe UI", 20, "bold"), 
            bootstyle="primary"
        ).pack(pady=(0, 10))
        
        ttk.Label(
            frame, 
            text="Unlock exclusive discounts and benefits", 
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(pady=(0, 25))

        # Current membership info
        current_level = getattr(self.customer, "membership_level", "None")
        current_info_frame = ttk.Labelframe(
            frame, 
            text="Current Membership", 
            padding=15,
            bootstyle="info"
        )
        current_info_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            current_info_frame, 
            text=f"Level: {current_level}", 
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")
        
        points = getattr(self.customer, "loyalty_points", 0)
        ttk.Label(
            current_info_frame, 
            text=f"Loyalty Points: {points}", 
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))

        # Membership upgrade section
        upgrade_frame = ttk.Labelframe(
            frame, 
            text="Upgrade to Premium", 
            padding=20,
            bootstyle="success"
        )
        upgrade_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            upgrade_frame, 
            text="Select membership level:", 
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))

        levels = ["Bronze (5% discount)", "Silver (10% discount)", "Gold (15% discount)"]
        self.level_var = tk.StringVar(value=levels[0])
        self.level_combo = ttk.Combobox(
            upgrade_frame, 
            textvariable=self.level_var, 
            values=levels, 
            state="readonly",
            font=("Segoe UI", 11)
        )
        self.level_combo.pack(fill="x", pady=(0, 15), ipady=7)

        ttk.Button(
            upgrade_frame, 
            text="⭐ Upgrade Membership", 
            command=self.upgrade_membership, 
            bootstyle="success",
            width=25
        ).pack(fill="x", ipady=8)

        # Student discount section
        student_frame = ttk.Labelframe(
            frame, 
            text="🎓 Student Discount", 
            padding=20,
            bootstyle="warning"
        )
        student_frame.pack(fill="x")
        
        ttk.Label(
            student_frame, 
            text="Are you a student? Get 20% off on all purchases!", 
            font=("Segoe UI", 10),
            wraplength=400,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))
        
        student_btn_text = "✅ Already Applied" if current_level == "Student" else "🎓 Get Student Discount (20%)"
        self.student_btn = ttk.Button(
            student_frame, 
            text=student_btn_text, 
            command=self.upgrade_to_student, 
            bootstyle="warning",
            width=25
        )
        self.student_btn.pack(fill="x", ipady=8)
        if current_level == "Student":
            self.student_btn.config(state="disabled", bootstyle="secondary")

    def upgrade_membership(self):
        selection = self.level_var.get().strip()
        if not selection:
            Messagebox.show_error("Please select a membership level.", "Error", parent=self)
            return
        new_level = selection.split(" ")[0]  # "Bronze (5%)" -> "Bronze"

        try:
            ok = db.update_customer_membership(getattr(self.customer, "_customer_id", getattr(self.customer, "customer_id", None)), new_level)
        except Exception as e:
            ok = False
            print("Error updating membership in DB:", e)

        if ok:
            Messagebox.show_info(f"Membership upgraded to {new_level}!", "Success", parent=self)
            # ask main app to refresh customer info if available
            if hasattr(self.parent, "update_customer_info"):
                try:
                    self.parent.update_customer_info()
                except Exception:
                    pass
            self.destroy()
        else:
            Messagebox.show_error("Failed to upgrade membership.", "Error", parent=self)

    def upgrade_to_student(self):
        try:
            ok = db.upgrade_to_student_membership(getattr(self.customer, "_customer_id", getattr(self.customer, "customer_id", None)))
        except Exception as e:
            ok = False
            print("Error upgrading to student membership:", e)

        if ok:
            Messagebox.show_info("Student membership (20% discount) applied!", "Success", parent=self)
            if hasattr(self.parent, "update_customer_info"):
                try:
                    self.parent.update_customer_info()
                except Exception:
                    pass
            self.destroy()
        else:
            Messagebox.show_error("Failed to apply student membership.", "Error", parent=self)
