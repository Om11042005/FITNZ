# File: FITNZ/payment_ui.py
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as bs
from ttkbootstrap.dialogs import Messagebox
from datetime import datetime
import re
from .product_forms import AddProductPage, EditProductPage

# Import your DB function (adjust relative import if package structure differs)
from . import database_mysql as db

class PaymentDialog(bs.Toplevel):
    """
    Modal dialog for entering card details and performing a simulated payment.
    On success, it will call db.process_sale(...) with provided sale details.
    """

    def __init__(self, parent, cart, customer_obj=None, user_obj=None,
                 points_redeemed=0, student_discount_applied=False, delivery_date=None):
        super().__init__(parent)
        self.parent = parent
        self.cart = cart
        self.customer_obj = customer_obj
        self.user_obj = user_obj
        self.points_redeemed = points_redeemed
        self.student_discount_applied = student_discount_applied
        self.delivery_date = delivery_date or (datetime.now().date())

        self.title("Payment — Enter Card Details")
        self.transient(parent)
        self.grab_set()
        self.minsize(420, 360)

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.result = None

    def create_widgets(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text="Enter Card Details", font=("Helvetica", 14, "bold")).pack(pady=(0,12))

        g = ttk.Frame(frm)
        g.pack(fill='x', padx=8, pady=4)

        ttk.Label(g, text="Cardholder Name:").grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(g); self.ent_name.grid(row=0, column=1, sticky="ew", padx=6)
        g.columnconfigure(1, weight=1)

        ttk.Label(g, text="Card Number:").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.ent_number = ttk.Entry(g); self.ent_number.grid(row=1, column=1, sticky="ew", padx=6, pady=(8,0))
        self.ent_number.insert(0, "")

        ttk.Label(g, text="Expiry (MM/YY):").grid(row=2, column=0, sticky="w", pady=(8,0))
        self.ent_expiry = ttk.Entry(g, width=10); self.ent_expiry.grid(row=2, column=1, sticky="w", padx=6, pady=(8,0))

        ttk.Label(g, text="CVV:").grid(row=3, column=0, sticky="w", pady=(8,0))
        self.ent_cvv = ttk.Entry(g, width=6, show="*"); self.ent_cvv.grid(row=3, column=1, sticky="w", padx=6, pady=(8,0))

        # Summary / amount display
        total, gst = self.calc_totals()
        ttk.Label(frm, text=f"Total: ${total:,.2f}    GST: ${gst:,.2f}", font=("Helvetica", 12)).pack(pady=(12,0))

        btns = ttk.Frame(frm)
        btns.pack(fill='x', pady=14)
        ttk.Button(btns, text="Pay Now", command=self.on_pay).pack(side='left', padx=4)
        ttk.Button(btns, text="Cancel", bootstyle="secondary", command=self.on_cancel).pack(side='right', padx=4)

        # small note about security
        ttk.Label(frm, text="(Demo payment — no card details are saved. For real payments, integrate a PCI-compliant gateway like Stripe/PayPal.)",
                  wraplength=380, font=("Helvetica", 9), foreground="gray").pack(pady=(6,0))

    def calc_totals(self):
        """Compute total and gst from cart items. Cart items expected to be dicts/objects with unit_price and qty/quantity."""
        total = 0.0
        gst = 0.0
        for it in self.cart:
            price = getattr(it, "unit_price", None) or getattr(it, "price", None) or (it.get("unit_price") if isinstance(it, dict) else 0)
            qty = getattr(it, "qty", None) or getattr(it, "quantity", None) or (it.get("qty") if isinstance(it, dict) else 1)
            # If item has gst_rate, use it; else default 15%
            gst_rate = getattr(it, "gst_rate", None) or (it.get("gst_rate") if isinstance(it, dict) else 0.15)
            line = float(price) * int(qty)
            total += line * (1 + float(gst_rate))
            gst += line * float(gst_rate)
        return total, gst

    # --- Validation helpers ---
    def luhn_check(self, card_number: str) -> bool:
        n = re.sub(r"\D", "", card_number)
        if len(n) < 12: 
            return False
        def digits_of(x): return [int(d) for d in x]
        digits = digits_of(n)
        odd_sum = sum(digits[-1::-2])
        even_sum = sum(sum(divmod(2*d, 10)) for d in digits[-2::-2])
        return (odd_sum + even_sum) % 10 == 0

    def validate_expiry(self, mm_yy: str) -> bool:
        try:
            mm_yy = mm_yy.strip()
            m, y = mm_yy.split("/")
            m = int(m); y = int(y)
            # normalize two-digit year to 2000+
            if y < 100:
                y += 2000
            exp = datetime(y, m, 1)
            now = datetime.now()
            # expire end of month: allow if current date <= last day of month
            return exp.replace(day=28) >= now.replace(day=28) or (y > now.year or (y==now.year and m>=now.month))
        except Exception:
            return False

    def validate_cvv(self, cvv: str) -> bool:
        return bool(re.fullmatch(r"\d{3,4}", cvv.strip()))

    # --- Payment processing (simulated) ---
    def on_pay(self):
        name = self.ent_name.get().strip()
        number = self.ent_number.get().strip()
        expiry = self.ent_expiry.get().strip()
        cvv = self.ent_cvv.get().strip()

        if not name:
            Messagebox.show_error("Cardholder name is required.", "Validation Error", parent=self); return
        if not number or not self.luhn_check(number):
            Messagebox.show_error("Invalid card number.", "Validation Error", parent=self); return
        if not expiry or not self.validate_expiry(expiry):
            Messagebox.show_error("Invalid expiry (use MM/YY).", "Validation Error", parent=self); return
        if not self.validate_cvv(cvv):
            Messagebox.show_error("Invalid CVV (3 or 4 digits).", "Validation Error", parent=self); return

        # simulate contacting payment gateway
        Messagebox.show_info("Processing payment... (demo)", "Processing", parent=self)
        self.after(800, self._complete_payment)  # small simulated delay

    def _complete_payment(self):
        """
        Here you'd call a real payment gateway. We'll simulate success.
        On success, call db.process_sale and close dialog.
        """
        # Simulate a successful payment result
        success = True

        if success:
            # Persist sale via your db API (match your code)
            try:
                # db.process_sale(customer_obj, cart, points_redeemed, student_discount_applied, delivery_date)
                # ensure proper args — these come from constructor
                ok = db.process_sale(self.customer_obj, self.cart, self.points_redeemed,
                                     self.student_discount_applied, self.delivery_date)
                if ok:
                    Messagebox.show_info("Payment successful. Sale recorded.", "Success", parent=self)
                else:
                    Messagebox.show_error("Payment succeeded but saving sale failed.", "DB Error", parent=self)
            except Exception as e:
                Messagebox.show_error(f"Payment succeeded but error saving sale: {e}", "Error", parent=self)
            self.result = True
            self.destroy()
        else:
            Messagebox.show_error("Payment failed. Please try again with a different card or contact support.", "Payment Failed", parent=self)
            self.result = False

    def on_cancel(self):
        self.result = False
        self.destroy()

