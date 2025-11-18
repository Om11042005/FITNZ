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
        self.parent = parent  # MainAppPage
        # Keep a shallow copy of cart so modifications here don't unexpectedly mutate outside
        self.cart = list(cart)
        self.customer = customer

        # State
        self.points_to_redeem = 0
        self.student_discount_applied = False
        self.total = 0.0

        # Window setup
        self.title("My Shopping Cart")
        self.geometry("640x560")
        self.resizable(True, True)

        # Layout root
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ttk.Frame(self, padding=16)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        header = ttk.Label(main_frame, text="My Cart", font=("Helvetica", 16, "bold"), bootstyle="primary")
        header.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Cart area
        cart_frame = ttk.Frame(main_frame)
        cart_frame.grid(row=1, column=0, sticky="nsew")
        cart_frame.grid_rowconfigure(0, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)

        cols = ("name", "price")
        self.cart_tree = ttk.Treeview(cart_frame, columns=cols, show="headings", bootstyle="primary")
        self.cart_tree.heading("name", text="Product Name")
        self.cart_tree.heading("price", text="Price")
        self.cart_tree.column("name", width=380, anchor="w")
        self.cart_tree.column("price", width=120, anchor="e")
        self.cart_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        vsb = ttk.Scrollbar(cart_frame, orient="vertical", command=self.cart_tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.cart_tree.configure(yscrollcommand=vsb.set)

        buttons_row = ttk.Frame(cart_frame)
        buttons_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        buttons_row.grid_columnconfigure(0, weight=1)
        ttk.Button(buttons_row, text="Remove Selected", command=self.remove_item, bootstyle="danger-outline").grid(row=0, column=0, sticky="w")

        # Summary frame
        summary_frame = ttk.Labelframe(main_frame, text="Order Summary", padding=12, bootstyle="info")
        summary_frame.grid(row=2, column=0, sticky="ew", pady=12)
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(1, weight=0)

        self.subtotal_label = ttk.Label(summary_frame, text="Subtotal: $0.00")
        self.subtotal_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        self.discount_label = ttk.Label(summary_frame, text="Discount: $0.00")
        self.discount_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        self.total_label = ttk.Label(summary_frame, text="Total: $0.00", font=("Helvetica", 12, "bold"))
        self.total_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=6)

        # Points entry and redeem button
        points_container = ttk.Frame(summary_frame)
        points_container.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        points_container.grid_columnconfigure(0, weight=1)
        points_container.grid_columnconfigure(1, weight=0)

        self.points_entry = ttk.Entry(points_container)
        self.points_entry.grid(row=0, column=0, sticky="ew", ipady=4)
        self.points_entry.insert(0, "0")

        max_points = getattr(self.customer, "loyalty_points", 0)
        ttk.Button(points_container, text=f"Redeem Points (Max: {max_points})", command=self.apply_points, bootstyle="info-outline").grid(row=0, column=1, sticky="ew", padx=(8, 0))

        # Student discount button (only if not already student)
        if getattr(self.customer, "membership_level", "") != "Student":
            ttk.Button(summary_frame, text="Apply Student Discount (20%)", command=self.apply_student_discount, bootstyle="warning-outline").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        # Proceed to checkout button
        ttk.Button(main_frame, text="Proceed to Checkout", command=self.open_checkout, bootstyle="success", bootstyle_secondary=True).grid(row=3, column=0, sticky="ew", ipady=6)

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

        self.title("Checkout")
        self.geometry("420x360")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Bind Enter to process payment
        self.bind('<Return>', lambda event: self.process_payment())

        # Layout: title, form (middle), buttons (bottom)
        title = ttk.Label(self, text="Simulated Payment", font=("Helvetica", 16, "bold"), bootstyle="primary")
        title.pack(pady=(12, 6), side="top")

        form_frame = ttk.Frame(self, padding=12)
        form_frame.pack(expand=True, fill="both", side="top")

        ttk.Label(form_frame, text=f"Amount to pay: ${self.total:.2f}", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 8))

        ttk.Label(form_frame, text="Card Number:").pack(anchor="w")
        self.card_entry = ttk.Entry(form_frame)
        self.card_entry.pack(fill="x", pady=5, ipady=3)

        ttk.Label(form_frame, text="Expiry (MM/YY):").pack(anchor="w")
        self.expiry_entry = ttk.Entry(form_frame)
        self.expiry_entry.pack(fill="x", pady=5, ipady=3)

        ttk.Label(form_frame, text="CVV:").pack(anchor="w")
        self.cvv_entry = ttk.Entry(form_frame, show="*")
        self.cvv_entry.pack(fill="x", pady=5, ipady=3)

        # Buttons anchored at bottom
        button_container = ttk.Frame(self, padding=(12, 8))
        button_container.pack(side="bottom", fill="x")
        button_container.grid_columnconfigure((0, 1), weight=1)

        pay_text = f"Pay Now ${self.total:.2f}"
        ttk.Button(button_container, text=pay_text, command=self.process_payment, bootstyle="success").grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=6)
        ttk.Button(button_container, text="Cancel", command=self.on_close, bootstyle="secondary-outline").grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=6)

    def validate_payment_fields(self) -> bool:
        """Simple validation for card fields (simulated)."""
        card = (self.card_entry.get() or "").strip()
        expiry = (self.expiry_entry.get() or "").strip()
        cvv = (self.cvv_entry.get() or "").strip()

        if not card or not expiry or not cvv:
            Messagebox.show_error("Please fill in all payment fields.", "Missing Details", parent=self)
            return False
        # Basic numeric checks (not secure, just simulated)
        if not card.isdigit() or not cvv.isdigit():
            Messagebox.show_error("Card number and CVV must be numbers.", "Invalid Details", parent=self)
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
        Messagebox.show_info(
            f"Your order has been placed!\nEstimated Delivery: {delivery_date.strftime('%A, %B %d, %Y')}",
            "Payment Successful",
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

        self.title("Manage Membership")
        self.geometry("420x420")
        self.resizable(False, False)

        frame = ttk.Frame(self, padding=16)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="Upgrade Membership", font=("Helvetica", 16, "bold"), bootstyle="primary").pack(pady=10)

        current_level = getattr(self.customer, "membership_level", "None")
        ttk.Label(frame, text=f"Current Level: {current_level}", font=("Helvetica", 12)).pack(pady=5)

        ttk.Label(frame, text="Select new level:").pack(pady=(10, 6))

        levels = ["Bronze (5%)", "Silver (10%)", "Gold (15%)"]
        self.level_var = tk.StringVar(value=levels[0])
        self.level_combo = ttk.Combobox(frame, textvariable=self.level_var, values=levels, state="readonly")
        self.level_combo.pack(fill="x", pady=5, ipady=6)

        ttk.Button(frame, text="Upgrade Membership", command=self.upgrade_membership, bootstyle="success").pack(fill="x", ipady=6, pady=10)

        ttk.Separator(frame).pack(fill="x", pady=12)

        ttk.Label(frame, text="Are you a student?").pack(pady=(4, 6))
        student_btn_text = "Already Applied" if current_level == "Student" else "Get Student Discount (20%)"
        self.student_btn = ttk.Button(frame, text=student_btn_text, command=self.upgrade_to_student, bootstyle="info")
        self.student_btn.pack(fill="x", ipady=6)
        if current_level == "Student":
            self.student_btn.config(state="disabled")

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
