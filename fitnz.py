# dashboard.py (Cyborg Theme)
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

from database import get_equipment_rating, add_or_update_rating, connect_db
from cart import CartWindow
from login import login_window


class Dashboard(tk.Tk):
    def __init__(self, customer_id, customer_name):
        super().__init__()

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

        self.FONT_TITLE = ("Segoe UI", 16, "bold")
        self.FONT_WELCOME = ("Segoe UI", 14, "bold")
        self.FONT_NORMAL = ("Segoe UI", 10)
        self.FONT_SMALL = ("Segoe UI", 9)
        self.FONT_BUTTON = ("Segoe UI", 10, "bold")

        self.title("FIT NZ - Gym Equipment Store (Cyborg Edition)")
        self.state("zoomed")
        self.config(bg=self.BG_MAIN)
        self.customer_id = customer_id
        self.customer_name = customer_name

        # Logo
        try:
            img = Image.open("FITNZ.png")
            img = img.resize((60, 60))
            self.logo = ImageTk.PhotoImage(img)
        except Exception:
            self.logo = None

        # Header
        header = tk.Frame(self, bg=self.BG_HEADER)
        header.pack(fill="x", pady=(0, 5), padx=0, ipady=5)

        left_header = tk.Frame(header, bg=self.BG_HEADER)
        left_header.pack(side="left", padx=20)

        if self.logo:
            tk.Label(left_header, image=self.logo, bg=self.BG_HEADER).pack(side="left", padx=(0, 10))

        tk.Label(
            left_header,
            text=f"Welcome to FIT NZ, {customer_name}",
            bg=self.BG_HEADER,
            fg=self.ACCENT,
            font=self.FONT_WELCOME,
        ).pack(side="left")

        tk.Label(
            header,
            text="CYBORG GYM EQUIPMENT STORE",
            bg=self.BG_HEADER,
            fg=self.FG_MUTED,
            font=self.FONT_SMALL,
        ).pack(side="left", padx=30)

        right_header = tk.Frame(header, bg=self.BG_HEADER)
        right_header.pack(side="right", padx=20)

        cart_btn = tk.Button(
            right_header,
            text="🛒 Cart",
            bg=self.BG_HEADER,
            fg=self.FG_TEXT,
            font=self.FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            activebackground=self.BG_HEADER,
            activeforeground=self.ACCENT,
            command=self.open_cart,
        )
        cart_btn.pack(side="left", padx=10)
        self.add_hover_effect(cart_btn, self.BG_HEADER, "#111827")

        logout_btn = tk.Button(
            right_header,
            text="Log Out",
            bg=self.DANGER,
            fg=self.BG_MAIN,
            font=self.FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            activebackground="#DB295F",
            activeforeground=self.BG_MAIN,
            command=self.logout,
        )
        logout_btn.pack(side="left", padx=5)
        self.add_hover_effect(logout_btn, self.DANGER, "#DB295F")

        # Scrollable products frame
        container = tk.Frame(self, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True, pady=10, padx=10)

        self.canvas = tk.Canvas(
            container,
            bg=self.BG_MAIN,
            highlightthickness=0,
            bd=0,
        )
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.products_frame = tk.Frame(self.canvas, bg=self.BG_MAIN)

        self.products_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.products_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.load_equipment()

    # ---------- Hover helper ----------
    def add_hover_effect(self, widget, normal_bg, hover_bg):
        def on_enter(_):
            widget.config(bg=hover_bg)

        def on_leave(_):
            widget.config(bg=normal_bg)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------- Load Equipment ----------
    def load_equipment(self):
        db = connect_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT equipment_id, name, description, price, image_path FROM equipment WHERE is_active=1"
        )
        items = cursor.fetchall()
        db.close()

        if not items:
            tk.Label(
                self.products_frame,
                text="No equipment found!",
                bg=self.BG_MAIN,
                fg=self.FG_TEXT,
                font=("Segoe UI", 12, "bold"),
            ).pack(pady=20)
            return

        columns = 4
        for i, eq in enumerate(items):
            frame = tk.Frame(
                self.products_frame,
                bg=self.BG_CARD,
                padx=12,
                pady=12,
                highlightthickness=1,
                highlightbackground="#1F2937",
            )
            frame.grid(row=i // columns, column=i % columns, padx=10, pady=10, sticky="nsew")

            equipment_id, name, description, price, image_path = eq

            # Image
            try:
                if image_path and os.path.exists(image_path):
                    img = Image.open(image_path)
                else:
                    raise Exception("No image file")
                img = img.resize((140, 140))
                photo = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading image for {name}: {e}")
                from PIL import Image as PILImage
                img = PILImage.new("RGB", (140, 140), color="#111827")
                photo = ImageTk.PhotoImage(img)

            lbl_img = tk.Label(frame, image=photo, bg=self.BG_CARD)
            lbl_img.image = photo
            lbl_img.pack()
            lbl_img.bind("<Button-1>", lambda e, p=eq: self.open_equipment_detail(p))

            name_lbl = tk.Label(
                frame,
                text=name,
                bg=self.BG_CARD,
                fg=self.FG_TEXT,
                font=("Segoe UI", 10, "bold"),
            )
            name_lbl.pack(pady=(6, 2))
            name_lbl.bind("<Button-1>", lambda e, p=eq: self.open_equipment_detail(p))

            tk.Label(
                frame,
                text=f"Price: ${price:.2f}",
                bg=self.BG_CARD,
                fg=self.ACCENT,
                font=("Segoe UI", 10, "bold"),
            ).pack()

            # Buttons row
            btn_row = tk.Frame(frame, bg=self.BG_CARD)
            btn_row.pack(pady=(8, 0))

            view_btn = tk.Button(
                btn_row,
                text="View",
                font=self.FONT_BUTTON,
                bg=self.BG_SUBTLE,
                fg=self.FG_TEXT,
                relief="flat",
                cursor="hand2",
                activebackground="#111827",
                activeforeground=self.ACCENT,
                command=lambda p=eq: self.open_equipment_detail(p),
            )
            view_btn.pack(side="left", padx=4)
            self.add_hover_effect(view_btn, self.BG_SUBTLE, "#111827")

            add_btn = tk.Button(
                btn_row,
                text="Add 🛒",
                font=self.FONT_BUTTON,
                bg=self.ACCENT,
                fg=self.BG_MAIN,
                relief="flat",
                cursor="hand2",
                activebackground=self.ACCENT_DARK,
                activeforeground=self.BG_MAIN,
                command=lambda p=eq: self.add_to_cart(p),
            )
            add_btn.pack(side="left", padx=4)
            self.add_hover_effect(add_btn, self.ACCENT, self.ACCENT_DARK)

    # ---------- Equipment Detail ----------
    def open_equipment_detail(self, eq):
        equipment_id, name, description, price, image_path = eq

        win = tk.Toplevel(self)
        win.title(name)
        win.geometry("900x650")
        win.config(bg=self.BG_MAIN)

        # Header
        header = tk.Frame(win, bg=self.BG_HEADER)
        header.pack(fill="x", padx=0, pady=(0, 5))

        tk.Label(
            header,
            text=name,
            font=("Segoe UI", 18, "bold"),
            bg=self.BG_HEADER,
            fg=self.ACCENT,
        ).pack(side="left", padx=20, pady=10)

        tk.Label(
            header,
            text=f"${price:.2f}",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_HEADER,
            fg=self.SUCCESS,
        ).pack(side="right", padx=20, pady=10)

        # Top section (image + description)
        top = tk.Frame(win, bg=self.BG_MAIN)
        top.pack(fill="x", padx=20, pady=10)

        try:
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
            else:
                raise Exception("No image file")
            img = img.resize((260, 260))
            photo = ImageTk.PhotoImage(img)
        except Exception:
            from PIL import Image as PILImage
            img = PILImage.new("RGB", (260, 260), color="#111827")
            photo = ImageTk.PhotoImage(img)

        img_lbl = tk.Label(top, image=photo, bg=self.BG_MAIN)
        img_lbl.image = photo
        img_lbl.pack(side="left", padx=10, pady=10)

        desc_frame = tk.Frame(top, bg=self.BG_MAIN)
        desc_frame.pack(side="left", padx=10, pady=10, fill="x")

        tk.Label(
            desc_frame,
            text="Description",
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        desc = tk.Text(
            desc_frame,
            height=13,
            width=60,
            wrap="word",
            bg=self.BG_ENTRY,
            fg=self.FG_TEXT,
            relief="flat",
            font=self.FONT_NORMAL,
        )
        desc.insert("1.0", description or "No description available.")
        desc.config(state="disabled")
        desc.pack(fill="both")

        # Section: rating + reviews
        section = tk.Frame(win, bg=self.BG_MAIN)
        section.pack(fill="both", expand=True, padx=20, pady=10)

        meta_frame = tk.Frame(section, bg=self.BG_MAIN)
        meta_frame.pack(fill="x", pady=(0, 5))

        avg_var = tk.StringVar(value="Loading rating...")
        avg_lbl = tk.Label(
            meta_frame,
            textvariable=avg_var,
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
        )
        avg_lbl.pack(side="left")

        reviews_frame = tk.Frame(section, bg=self.BG_MAIN)
        reviews_frame.pack(fill="both", expand=True, pady=10)

        def refresh_rating_and_reviews():
            try:
                avg, cnt = get_equipment_rating(equipment_id)
                avg_var.set(f"Average rating: {avg:.1f} / 5  ({cnt} review{'s' if cnt != 1 else ''})")
            except Exception:
                avg_var.set("Average rating: N/A")

            for w in reviews_frame.winfo_children():
                w.destroy()

            try:
                db = connect_db()
                cur = db.cursor()
                cur.execute(
                    """
                    SELECT c.full_name, r.rating, COALESCE(r.comment,''), r.created_at
                    FROM equipment_ratings r
                    JOIN customers c ON c.customer_id = r.customer_id
                    WHERE r.equipment_id=%s
                    ORDER BY r.created_at DESC
                    LIMIT 10
                    """,
                    (equipment_id,),
                )
                rows = cur.fetchall()
                db.close()
            except Exception:
                rows = []

            if not rows:
                tk.Label(
                    reviews_frame,
                    text="No reviews yet.",
                    bg=self.BG_MAIN,
                    fg=self.FG_MUTED,
                    font=("Segoe UI", 11, "italic"),
                ).pack(anchor="w")
            else:
                for full_name, rating, comment, created_at in rows:
                    tk.Label(
                        reviews_frame,
                        text=f"{full_name} - {rating}/5",
                        bg=self.BG_MAIN,
                        fg=self.ACCENT,
                        font=("Segoe UI", 11, "bold"),
                    ).pack(anchor="w")
                    if comment:
                        tk.Label(
                            reviews_frame,
                            text=comment,
                            bg=self.BG_MAIN,
                            fg=self.FG_TEXT,
                            wraplength=700,
                            justify="left",
                            font=("Segoe UI", 10),
                        ).pack(anchor="w", pady=(0, 6))

        # Rating form
        form = tk.Frame(section, bg=self.BG_SUBTLE)
        form.pack(fill="x", pady=5, padx=0)

        tk.Label(
            form,
            text="Your rating (1-5):",
            bg=self.BG_SUBTLE,
            fg=self.FG_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=10, pady=10)

        rating_var = tk.IntVar(value=5)
        rating_spin = tk.Spinbox(
            form,
            from_=1,
            to=5,
            width=5,
            textvariable=rating_var,
            bg=self.BG_ENTRY,
            fg=self.FG_TEXT,
            insertbackground=self.ACCENT,
            relief="flat",
            justify="center",
        )
        rating_spin.pack(side="left")

        tk.Label(
            form,
            text="Comment:",
            bg=self.BG_SUBTLE,
            fg=self.FG_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(20, 5))

        comment_entry = tk.Entry(
            form,
            width=60,
            bg=self.BG_ENTRY,
            fg=self.FG_TEXT,
            insertbackground=self.ACCENT,
            relief="flat",
        )
        comment_entry.pack(side="left", padx=5)

        def submit_rating():
            try:
                r = int(rating_var.get())
            except Exception:
                messagebox.showerror("Error", "Rating must be a number between 1 and 5")
                return
            if r < 1 or r > 5:
                messagebox.showerror("Error", "Rating must be between 1 and 5")
                return

            cmt = comment_entry.get().strip()
            try:
                add_or_update_rating(self.customer_id, equipment_id, r, cmt if cmt else None)
                messagebox.showinfo("Thanks!", "Your rating has been submitted.")
                comment_entry.delete(0, tk.END)
                refresh_rating_and_reviews()
            except Exception as err:
                messagebox.showerror("Error", f"Unable to submit rating: {err}")

        submit_btn = tk.Button(
            form,
            text="Submit",
            bg=self.SUCCESS,
            fg=self.BG_MAIN,
            font=self.FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            activebackground="#059669",
            activeforeground=self.BG_MAIN,
            command=submit_rating,
        )
        submit_btn.pack(side="left", padx=10)
        self.add_hover_effect(submit_btn, self.SUCCESS, "#059669")

        refresh_rating_and_reviews()

    # ---------- Add to Cart ----------
    def add_to_cart(self, eq):
        equipment_id = eq[0]
        db = connect_db()
        cursor = db.cursor()
        try:
            db.start_transaction()
            cursor.execute(
                "SELECT stock, name FROM equipment WHERE equipment_id=%s FOR UPDATE",
                (equipment_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise Exception("Equipment not found.")
            stock, name = row
            if (stock or 0) <= 0:
                raise Exception(f"{name} is out of stock.")

            cursor.execute(
                "UPDATE equipment SET stock = stock - 1 WHERE equipment_id=%s",
                (equipment_id,),
            )

            cursor.execute(
                "SELECT quantity FROM cart WHERE customer_id=%s AND equipment_id=%s FOR UPDATE",
                (self.customer_id, equipment_id),
            )
            result = cursor.fetchone()
            if result:
                cursor.execute(
                    """
                    UPDATE cart
                    SET quantity = quantity + 1
                    WHERE customer_id=%s AND equipment_id=%s
                    """,
                    (self.customer_id, equipment_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO cart (customer_id, equipment_id, quantity) VALUES (%s, %s, %s)",
                    (self.customer_id, equipment_id, 1),
                )

            db.commit()
            messagebox.showinfo("Cart", f"Added {eq[1]} to cart!")
        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            messagebox.showerror("Cart", str(e))
        finally:
            db.close()

    def open_cart(self):
        CartWindow(self, self.customer_id)

    def logout(self):
        self.destroy()


def start_dashboard(customer_id, customer_name):
    app = Dashboard(customer_id, customer_name)
    app.mainloop()


if __name__ == "__main__":
    login_window(on_success=start_dashboard)
