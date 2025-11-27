# cart.py (Cyborg Theme)
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import io
import requests
import os

from checkout import CheckoutWindow
from database import connect_db


class CartWindow(tk.Toplevel):
    def __init__(self, parent, customer_id):
        super().__init__(parent)

        # ---------- Cyborg Theme Palette ----------
        self.BG_MAIN = "#050816"       # Deep space background
        self.BG_HEADER = "#0B1020"     # Header bar
        self.BG_CARD = "#0F172A"       # Cards / panels
        self.BG_ENTRY = "#111827"      # Inputs / text background
        self.BG_SUBTLE = "#1F2937"     # Sub-panels
        self.FG_TEXT = "#E5F0FF"       # Primary text
        self.FG_MUTED = "#9CA3AF"      # Secondary text
        self.ACCENT = "#00E5FF"        # Neon cyan
        self.ACCENT_DARK = "#0095A8"   # Darker cyan
        self.SUCCESS = "#10B981"       # Neon green
        self.DANGER = "#FF4B91"        # Pink/red accent

        self.FONT_TITLE = ("Segoe UI", 18, "bold")
        self.FONT_NORMAL = ("Segoe UI", 10)
        self.FONT_LABEL = ("Segoe UI", 11)
        self.FONT_BUTTON = ("Segoe UI", 10, "bold")

        self.title("Your Cart - FIT NZ (Cyborg Edition)")
        self.geometry("980x620")
        self.config(bg=self.BG_MAIN)
        self.customer_id = customer_id

        # ---------- Header ----------
        header = tk.Frame(self, bg=self.BG_HEADER)
        header.pack(fill="x", pady=(0, 5), padx=0)

        tk.Label(
            header,
            text="Your Cart 🛒",
            bg=self.BG_HEADER,
            fg=self.ACCENT,
            font=self.FONT_TITLE,
        ).pack(side="left", padx=20, pady=10)

        close_btn = tk.Button(
            header,
            text="Close",
            bg=self.DANGER,
            fg=self.BG_MAIN,
            font=self.FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            activebackground="#DB295F",
            activeforeground=self.BG_MAIN,
            command=self.destroy,
        )
        close_btn.pack(side="right", padx=20)
        self.add_hover_effect(close_btn, self.DANGER, "#DB295F")

        # ---------- Main Layout ----------
        main_frame = tk.Frame(self, bg=self.BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Left side: items list (with simple scroll)
        left_container = tk.Frame(main_frame, bg=self.BG_MAIN)
        left_container.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.items_canvas = tk.Canvas(
            left_container,
            bg=self.BG_MAIN,
            highlightthickness=0,
            bd=0,
        )
        items_scrollbar = tk.Scrollbar(
            left_container, orient="vertical", command=self.items_canvas.yview
        )
        self.items_frame = tk.Frame(self.items_canvas, bg=self.BG_MAIN)

        self.items_frame.bind(
            "<Configure>",
            lambda e: self.items_canvas.configure(scrollregion=self.items_canvas.bbox("all")),
        )

        self.items_canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        self.items_canvas.configure(yscrollcommand=items_scrollbar.set)

        self.items_canvas.pack(side="left", fill="both", expand=True)
        items_scrollbar.pack(side="right", fill="y")
        self.items_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Right side: checkout summary
        self.checkout_frame = tk.Frame(
            main_frame,
            bg=self.BG_CARD,
            width=320,
            height=500,
            highlightthickness=1,
            highlightbackground="#1F2937",
        )
        self.checkout_frame.pack(side="right", padx=(10, 0), pady=5, fill="y")
        self.checkout_frame.pack_propagate(False)

        tk.Label(
            self.checkout_frame,
            text="Checkout Summary",
            bg=self.BG_CARD,
            fg=self.FG_TEXT,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="nw", pady=10, padx=12)

        self.checkout_items = tk.Frame(self.checkout_frame, bg=self.BG_CARD)
        self.checkout_items.pack(anchor="nw", padx=12, pady=(0, 10), fill="both", expand=True)

        self.total_label = tk.Label(
            self.checkout_frame,
            text="Total: $0.00",
            bg=self.BG_CARD,
            fg=self.ACCENT,
            font=("Segoe UI", 14, "bold"),
        )
        self.total_label.pack(anchor="s", pady=(0, 10))

        proceed_btn = tk.Button(
            self.checkout_frame,
            text="Proceed to Checkout",
            bg=self.SUCCESS,
            fg=self.BG_MAIN,
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground="#059669",
            activeforeground=self.BG_MAIN,
            command=self.checkout,
        )
        proceed_btn.pack(side="bottom", pady=15, padx=12, fill="x")
        self.add_hover_effect(proceed_btn, self.SUCCESS, "#059669")

        self.load_cart()

    # ---------- Hover helper ----------
    def add_hover_effect(self, widget, normal_bg, hover_bg):
        def on_enter(_):
            widget.config(bg=hover_bg)

        def on_leave(_):
            widget.config(bg=normal_bg)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _on_mousewheel(self, event):
        self.items_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------- Load Cart Items ----------
    def load_cart(self):
        db = connect_db()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT c.cart_id, c.quantity, e.equipment_id, e.name, e.price, e.image_path
            FROM cart c
            JOIN equipment e ON c.equipment_id = e.equipment_id
            WHERE c.customer_id=%s
            """,
            (self.customer_id,),
        )
        cart_items = cursor.fetchall()
        db.close()

        # Clear frames
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        for widget in self.checkout_items.winfo_children():
            widget.destroy()

        if not cart_items:
            tk.Label(
                self.items_frame,
                text="Your cart is empty.\nBrowse the store to add some cyborg gear!",
                bg=self.BG_MAIN,
                fg=self.FG_MUTED,
                font=("Segoe UI", 12, "bold"),
                justify="left",
            ).pack(anchor="nw", pady=20, padx=10)
            self.total_label.config(text="Total: $0.00")
            self.total_price = 0
            return

        self.total_price = 0
        for item in cart_items:
            cart_id, quantity, equipment_id, name, price, image_path = item
            self.total_price += price * quantity

            frame = tk.Frame(
                self.items_frame,
                bg=self.BG_CARD,
                pady=10,
                padx=10,
                highlightthickness=1,
                highlightbackground="#1F2937",
            )
            frame.pack(anchor="nw", fill="x", pady=6, padx=4)

            # Load image (local or URL)
            try:
                if image_path and os.path.exists(image_path):
                    img = Image.open(image_path)
                else:
                    if image_path:
                        response = requests.get(image_path, timeout=5)
                        img = Image.open(io.BytesIO(response.content))
                    else:
                        raise Exception("No image path")
                img = img.resize((90, 90))
                photo = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading image for {name}: {e}")
                from PIL import Image as PILImage
                img = PILImage.new("RGB", (90, 90), color="#111827")
                photo = ImageTk.PhotoImage(img)

            lbl_img = tk.Label(frame, image=photo, bg=self.BG_CARD)
            lbl_img.image = photo
            lbl_img.pack(side="left")

            info_frame = tk.Frame(frame, bg=self.BG_CARD)
            info_frame.pack(side="left", padx=10, fill="x", expand=True)

            tk.Label(
                info_frame,
                text=name,
                bg=self.BG_CARD,
                fg=self.FG_TEXT,
                font=("Segoe UI", 12, "bold"),
            ).pack(anchor="w")
            tk.Label(
                info_frame,
                text=f"Price: ${price:.2f}",
                bg=self.BG_CARD,
                fg=self.ACCENT,
                font=("Segoe UI", 11),
            ).pack(anchor="w")
            tk.Label(
                info_frame,
                text=f"Quantity: {quantity}",
                bg=self.BG_CARD,
                fg=self.FG_MUTED,
                font=("Segoe UI", 11),
            ).pack(anchor="w")

            # Buttons
            btn_frame = tk.Frame(info_frame, bg=self.BG_CARD)
            btn_frame.pack(anchor="w", pady=6)

            plus_btn = tk.Button(
                btn_frame,
                text="+",
                bg=self.BG_SUBTLE,
                fg=self.FG_TEXT,
                font=("Segoe UI", 11, "bold"),
                width=2,
                relief="flat",
                cursor="hand2",
                activebackground="#111827",
                activeforeground=self.ACCENT,
                command=lambda cid=cart_id: self.add_quantity(cid),
            )
            plus_btn.pack(side="left", padx=(0, 8))
            self.add_hover_effect(plus_btn, self.BG_SUBTLE, "#111827")

            remove_btn = tk.Button(
                btn_frame,
                text="Remove",
                bg=self.DANGER,
                fg=self.BG_MAIN,
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                cursor="hand2",
                activebackground="#DB295F",
                activeforeground=self.BG_MAIN,
                command=lambda cid=cart_id: self.remove_item(cid),
            )
            remove_btn.pack(side="left")
            self.add_hover_effect(remove_btn, self.DANGER, "#DB295F")

            # Checkout summary line
            tk.Label(
                self.checkout_items,
                text=f"{name} × {quantity} ........... ${price * quantity:.2f}",
                bg=self.BG_CARD,
                fg=self.FG_TEXT,
                font=("Segoe UI", 11),
            ).pack(anchor="w")

        self.total_label.config(text=f"Total: ${self.total_price:.2f}")

    # ---------- Add Quantity ----------
    def add_quantity(self, cart_id):
        db = connect_db()
        cursor = db.cursor()
        try:
            db.start_transaction()
            cursor.execute(
                "SELECT equipment_id FROM cart WHERE cart_id=%s AND customer_id=%s FOR UPDATE",
                (cart_id, self.customer_id),
            )
            row = cursor.fetchone()
            if not row:
                raise Exception("Cart item not found.")
            equipment_id = row[0]

            cursor.execute(
                "SELECT stock, name FROM equipment WHERE equipment_id=%s FOR UPDATE",
                (equipment_id,),
            )
            prow = cursor.fetchone()
            if not prow:
                raise Exception("Equipment not found.")
            stock, name = prow
            if (stock or 0) <= 0:
                raise Exception(f"{name} is out of stock.")

            cursor.execute(
                "UPDATE equipment SET stock = stock - 1 WHERE equipment_id=%s",
                (equipment_id,),
            )
            cursor.execute(
                "UPDATE cart SET quantity = quantity + 1 WHERE cart_id=%s",
                (cart_id,),
            )
            db.commit()
        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            messagebox.showerror("Cart", str(e))
        finally:
            db.close()
            self.load_cart()

    # ---------- Remove Item ----------
    def remove_item(self, cart_id):
        db = connect_db()
        cursor = db.cursor()
        try:
            db.start_transaction()
            cursor.execute(
                """
                SELECT equipment_id, quantity
                FROM cart
                WHERE cart_id=%s AND customer_id=%s FOR UPDATE
                """,
                (cart_id, self.customer_id),
            )
            row = cursor.fetchone()
            if row:
                equipment_id, qty = row
                cursor.execute(
                    "UPDATE equipment SET stock = stock + %s WHERE equipment_id=%s",
                    (qty, equipment_id),
                )
                cursor.execute("DELETE FROM cart WHERE cart_id=%s", (cart_id,))
            db.commit()
        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            messagebox.showerror("Cart", str(e))
        finally:
            db.close()
            self.load_cart()

    # ---------- Checkout ----------
    def checkout(self):
        if getattr(self, "total_price", 0) == 0:
            messagebox.showwarning(
                "Cart Empty",
                "Your cart is empty. Add items before checkout!"
            )
            return
        CheckoutWindow(self, self.customer_id)
