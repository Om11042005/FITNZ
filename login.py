# login.py (Cyborg Theme)
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import mysql.connector

from database import increment_login_counter, connect_db
from admin import AdminPanel


def login_window(on_success):
    # ---------- Cyborg Theme Palette ----------
    BG_MAIN = "#050816"         # Deep space background
    BG_CARD = "#0B1020"         # Panel / card background
    BG_ENTRY = "#131A2A"        # Input fields background
    FG_TEXT = "#E5F0FF"         # Primary text
    FG_MUTED = "#8F9BB3"        # Secondary text
    ACCENT = "#00E5FF"          # Neon cyan
    ACCENT_DARK = "#0095A8"     # Darker cyan for hover / active
    DANGER = "#FF4B91"          # Pink/red for errors or emphasis

    FONT_TITLE = ("Segoe UI", 22, "bold")
    FONT_SUBTITLE = ("Segoe UI", 11, "bold")
    FONT_NORMAL = ("Segoe UI", 10)
    FONT_BUTTON = ("Segoe UI", 11, "bold")

    # ---------- Main Window ----------
    root = tk.Tk()
    root.title("FIT NZ Login - Cyborg Edition")
    root.state("zoomed")
    root.config(bg=BG_MAIN)

    # ---------- Load Logo ----------
    try:
        logo_img = Image.open("FITNZ.png")  # update with your logo file
        logo_img = logo_img.resize((140, 140))
        logo = ImageTk.PhotoImage(logo_img)
        root.logo_ref = logo  # keep a reference to avoid GC
    except Exception:
        logo = None

    # ---------- Switch Frames ----------
    def open_register():
        login_frame.pack_forget()
        register_frame.pack(fill="both", expand=True, pady=10)

    def open_login():
        register_frame.pack_forget()
        login_frame.pack(pady=20)

    # ---------- Login Function ----------
    def login_user():
        email = email_entry.get().strip()
        password = password_entry.get().strip()

        if not email or not password:
            messagebox.showwarning("Input Error", "Please fill all fields!")
            return

        # Simple admin backdoor
        if email == "admin" and password == "admin":
            root.destroy()
            admin_panel = AdminPanel()
            admin_panel.mainloop()
            return

        db = connect_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT customer_id, full_name FROM customers WHERE email=%s AND password=%s",
                (email, password),
            )
            row = cursor.fetchone()
        finally:
            db.close()

        if row:
            customer_id, full_name = row
            try:
                increment_login_counter(customer_id)
            except Exception:
                pass
            root.destroy()
            on_success(customer_id, full_name)
        else:
            messagebox.showerror("Error", "Invalid email or password")

    # ---------- Forgot Password ----------
    def forgot_password():
        email = simpledialog.askstring("Forgot Password", "Enter your registered email:")
        if email is None:
            return
        email = email.strip()
        if not email:
            messagebox.showwarning("Input Error", "Email cannot be empty.")
            return

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute("SELECT password FROM customers WHERE email=%s", (email,))
            row = cursor.fetchone()
            db.close()
            if row:
                saved_password = row[0]
                messagebox.showinfo("Your Password", f"Password for {email}:\n{saved_password}")
            else:
                messagebox.showerror("Not Found", "No customer found with that email.")
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Database Error: {err}")

    # ---------- Register Function ----------
    def register_customer():
        full_name = full_name_entry.get().strip()
        email = reg_email_entry.get().strip()
        password = reg_password_entry.get().strip()
        address = address_entry.get().strip()
        phone = phone_entry.get().strip()

        if not full_name or not email or not password:
            messagebox.showwarning(
                "Input Error", "Full Name, Email and Password are required!"
            )
            return

        try:
            db = connect_db()
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO customers (full_name, email, password, phone, address)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (full_name, email, password, phone, address),
            )
            db.commit()
            db.close()
            messagebox.showinfo("Success", "Registration successful! You can now log in.")
            open_login()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Database Error: {err}")

    # ---------- Helper: Button Hover Effect ----------
    def add_hover_effect(widget, normal_bg, hover_bg):
        def on_enter(_):
            widget.config(bg=hover_bg)

        def on_leave(_):
            widget.config(bg=normal_bg)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    # ---------- Login Frame ----------
    login_frame = tk.Frame(root, bg=BG_MAIN)

    card = tk.Frame(login_frame, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=ACCENT)
    card.pack(pady=40, padx=20)

    if logo:
        tk.Label(card, image=logo, bg=BG_CARD).pack(pady=(20, 10))

    tk.Label(
        card,
        text="FIT NZ – Member Login",
        font=FONT_TITLE,
        bg=BG_CARD,
        fg=ACCENT,
    ).pack(pady=(5, 15))

    tk.Label(
        card,
        text="Enter your credentials to access the cyborg fitness system.",
        font=FONT_NORMAL,
        bg=BG_CARD,
        fg=FG_MUTED,
    ).pack(pady=(0, 20))

    # Email
    tk.Label(
        card,
        text="Email",
        font=FONT_SUBTITLE,
        bg=BG_CARD,
        fg=FG_TEXT,
    ).pack(anchor="w", padx=40, pady=(0, 5))

    email_entry = tk.Entry(
        card,
        width=35,
        bd=0,
        relief="flat",
        bg=BG_ENTRY,
        fg=FG_TEXT,
        insertbackground=ACCENT,
        font=FONT_NORMAL,
        highlightthickness=1,
        highlightbackground="#1F2A3A",
        highlightcolor=ACCENT,
    )
    email_entry.pack(pady=(0, 15), ipady=6, padx=40)

    # Password
    tk.Label(
        card,
        text="Password",
        font=FONT_SUBTITLE,
        bg=BG_CARD,
        fg=FG_TEXT,
    ).pack(anchor="w", padx=40, pady=(0, 5))

    password_entry = tk.Entry(
        card,
        show="*",
        width=35,
        bd=0,
        relief="flat",
        bg=BG_ENTRY,
        fg=FG_TEXT,
        insertbackground=ACCENT,
        font=FONT_NORMAL,
        highlightthickness=1,
        highlightbackground="#1F2A3A",
        highlightcolor=ACCENT,
    )
    password_entry.pack(pady=(0, 20), ipady=6, padx=40)

    # Login Button
    login_btn = tk.Button(
        card,
        text="LOGIN",
        bg=ACCENT,
        fg=BG_MAIN,
        font=FONT_BUTTON,
        width=20,
        relief="flat",
        activebackground=ACCENT_DARK,
        activeforeground=BG_MAIN,
        cursor="hand2",
        pady=5,
        bd=0,
    )
    login_btn.config(command=login_user)
    login_btn.pack(pady=(0, 10))
    add_hover_effect(login_btn, ACCENT, ACCENT_DARK)

    # Register Button
    register_btn = tk.Button(
        card,
        text="Create New Account",
        bg=BG_CARD,
        fg=ACCENT,
        font=FONT_BUTTON,
        relief="flat",
        activebackground=BG_CARD,
        activeforeground=ACCENT_DARK,
        cursor="hand2",
        pady=2,
        bd=0,
    )
    register_btn.config(command=open_register)
    register_btn.pack(pady=(0, 8))
    add_hover_effect(register_btn, BG_CARD, "#151B2C")

    # Forgot Password
    forgot_btn = tk.Button(
        card,
        text="Forgot Password?",
        bg=BG_CARD,
        fg=FG_MUTED,
        font=("Segoe UI", 9, "underline"),
        relief="flat",
        activebackground=BG_CARD,
        activeforeground=ACCENT,
        cursor="hand2",
        bd=0,
    )
    forgot_btn.config(command=forgot_password)
    forgot_btn.pack(pady=(0, 20))
    add_hover_effect(forgot_btn, BG_CARD, "#151B2C")

    login_frame.pack(pady=20)

    # ---------- Register Frame (SCROLLABLE) ----------
    register_frame = tk.Frame(root, bg=BG_MAIN)

    # Canvas + Scrollbar
    reg_canvas = tk.Canvas(register_frame, bg=BG_MAIN, highlightthickness=0)
    reg_canvas.pack(side="left", fill="both", expand=True)

    reg_scrollbar = tk.Scrollbar(register_frame, orient="vertical", command=reg_canvas.yview)
    reg_scrollbar.pack(side="right", fill="y")

    reg_canvas.configure(yscrollcommand=reg_scrollbar.set)

    # Inner frame inside canvas
    reg_inner = tk.Frame(reg_canvas, bg=BG_MAIN)
    reg_canvas.create_window((0, 0), window=reg_inner, anchor="nw")

    # Make scrollregion adjust to content
    def on_reg_configure(event):
        reg_canvas.configure(scrollregion=reg_canvas.bbox("all"))

    reg_inner.bind("<Configure>", on_reg_configure)

    # Optional: mouse wheel scroll
    def _on_mousewheel(event):
        # For Windows
        reg_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    reg_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ------ Registration Card inside inner frame ------
    reg_card = tk.Frame(reg_inner, bg=BG_CARD, bd=0, highlightthickness=1, highlightbackground=ACCENT)
    reg_card.pack(pady=40, padx=20)  # reduced padding so it fits easier

    if logo:
        tk.Label(reg_card, image=logo, bg=BG_CARD).pack(pady=(20, 10))

    tk.Label(
        reg_card,
        text="FIT NZ – New Member",
        font=FONT_TITLE,
        bg=BG_CARD,
        fg=ACCENT,
    ).pack(pady=(5, 10))

    tk.Label(
        reg_card,
        text="Join the cyborg fitness community. Fill in your details below.",
        font=FONT_NORMAL,
        bg=BG_CARD,
        fg=FG_MUTED,
        wraplength=500,
        justify="center"
    ).pack(pady=(0, 15))

    def make_labeled_entry(parent, label_text):
        tk.Label(
            parent,
            text=label_text,
            font=FONT_SUBTITLE,
            bg=BG_CARD,
            fg=FG_TEXT,
        ).pack(anchor="w", padx=40, pady=(0, 3))

        entry = tk.Entry(
            parent,
            width=35,
            bd=0,
            relief="flat",
            bg=BG_ENTRY,
            fg=FG_TEXT,
            insertbackground=ACCENT,
            font=FONT_NORMAL,
            highlightthickness=1,
            highlightbackground="#1F2A3A",
            highlightcolor=ACCENT,
        )
        entry.pack(pady=(0, 10), ipady=5, padx=40)
        return entry

    full_name_entry = make_labeled_entry(reg_card, "Full Name")
    reg_email_entry = make_labeled_entry(reg_card, "Email")

    tk.Label(
        reg_card,
        text="Password",
        font=FONT_SUBTITLE,
        bg=BG_CARD,
        fg=FG_TEXT,
    ).pack(anchor="w", padx=40, pady=(0, 3))

    reg_password_entry = tk.Entry(
        reg_card,
        show="*",
        width=35,
        bd=0,
        relief="flat",
        bg=BG_ENTRY,
        fg=FG_TEXT,
        insertbackground=ACCENT,
        font=FONT_NORMAL,
        highlightthickness=1,
        highlightbackground="#1F2A3A",
        highlightcolor=ACCENT,
    )
    reg_password_entry.pack(pady=(0, 10), ipady=5, padx=40)

    address_entry = make_labeled_entry(reg_card, "Address")
    phone_entry = make_labeled_entry(reg_card, "Phone No")

    reg_btn = tk.Button(
        reg_card,
        text="REGISTER",
        bg=ACCENT,
        fg=BG_MAIN,
        font=FONT_BUTTON,
        width=20,
        relief="flat",
        activebackground=ACCENT_DARK,
        activeforeground=BG_MAIN,
        cursor="hand2",
        pady=5,
        bd=0,
        command=register_customer,
    )
    reg_btn.pack(pady=(10, 5))
    add_hover_effect(reg_btn, ACCENT, ACCENT_DARK)

    back_btn = tk.Button(
        reg_card,
        text="Back to Login",
        bg=BG_CARD,
        fg=ACCENT,
        font=FONT_BUTTON,
        relief="flat",
        activebackground=BG_CARD,
        activeforeground=ACCENT_DARK,
        cursor="hand2",
        pady=2,
        bd=0,
        command=open_login,
    )
    back_btn.pack(pady=(0, 15))
    add_hover_effect(back_btn, BG_CARD, "#151B2C")

    root.mainloop()
