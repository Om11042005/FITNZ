# admin.py (Cyborg Theme)
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import mysql.connector
from tkinter import messagebox, filedialog

from database import (
    get_most_sold_equipment,
    get_least_sold_equipment,
    connect_db,
)

# Predefined categories for FIT NZ gym equipment
CATEGORIES = [
    "Cardio Machines",
    "Strength Equipment",
    "Free Weights",
    "Resistance Bands",
    "Accessories",
    "Mats & Flooring",
]


def get_category_id(category_name):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT category_id FROM equipment_category WHERE name=%s", (category_name,))
    row = cursor.fetchone()

    if row:
        db.close()
        return row[0]

    cursor.execute("INSERT INTO equipment_category(name) VALUES(%s)", (category_name,))
    db.commit()
    new_id = cursor.lastrowid

    db.close()
    return new_id


class AdminPanel(tk.Tk):
    def __init__(self):
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
        self.DANGER = "#FF4B91"        # Pink/red
        self.WARNING = "#F59E0B"       # Amber

        self.FONT_TITLE = ("Segoe UI", 22, "bold")
        self.FONT_SUBTITLE = ("Segoe UI", 14, "bold")
        self.FONT_LABEL = ("Segoe UI", 10)
        self.FONT_BUTTON = ("Segoe UI", 11, "bold")

        self.title("FIT NZ - Admin Panel (Cyborg Edition)")
        self.state("zoomed")
        self.config(bg=self.BG_MAIN)

        # ttk style for dark tables
        self.style = ttk.Style(self)
        self._configure_treeview_style()

        # Logo
        try:
            img = Image.open("FITNZ.png")
            img = img.resize((70, 70))
            self.logo = ImageTk.PhotoImage(img)
        except Exception:
            self.logo = None

        # ---------- Header ----------
        header = tk.Frame(self, bg=self.BG_HEADER)
        header.pack(fill="x", padx=0, pady=(0, 8))

        left_header = tk.Frame(header, bg=self.BG_HEADER)
        left_header.pack(side="left", padx=20)

        if self.logo:
            tk.Label(left_header, image=self.logo, bg=self.BG_HEADER).pack(side="left", padx=(0, 10))

        tk.Label(
            left_header,
            text="FIT NZ Admin Console",
            font=self.FONT_TITLE,
            bg=self.BG_HEADER,
            fg=self.ACCENT,
        ).pack(side="left")

        tk.Label(
            header,
            text="CYBORG CONTROL CENTER",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_HEADER,
            fg=self.FG_MUTED,
        ).pack(side="left", padx=25)

        exit_btn = tk.Button(
            header,
            text="Exit",
            bg=self.DANGER,
            fg=self.BG_MAIN,
            font=self.FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            activebackground="#DB295F",
            activeforeground=self.BG_MAIN,
            command=self.destroy,
        )
        exit_btn.pack(side="right", padx=20)
        self.add_hover_effect(exit_btn, self.DANGER, "#DB295F")

        # ---------- Top Buttons ----------
        btn_frame = tk.Frame(self, bg=self.BG_MAIN)
        btn_frame.pack(pady=10)

        def make_top_btn(text, bg, command, col):
            btn = tk.Button(
                btn_frame,
                text=text,
                bg=bg,
                fg=self.BG_MAIN if bg in (self.ACCENT, self.SUCCESS, self.DANGER, self.WARNING) else self.FG_TEXT,
                font=self.FONT_BUTTON,
                relief="flat",
                cursor="hand2",
                activebackground=self.ACCENT_DARK if bg == self.ACCENT else bg,
                activeforeground=self.BG_MAIN,
                width=16,
                pady=4,
                command=command,
            )
            btn.grid(row=0, column=col, padx=8)
            self.add_hover_effect(btn, bg, self._hover_color(bg))

        make_top_btn("Add Equipment", self.SUCCESS, self.add_equipment_window, 0)
        make_top_btn("Update Equipment", self.WARNING, self.update_equipment_window, 1)
        make_top_btn("Delete Equipment", self.DANGER, self.delete_equipment_window, 2)
        make_top_btn("Manage Customers", self.ACCENT, self.open_customers_window, 3)
        make_top_btn("Insights Dashboard", self.BG_SUBTLE, self.open_insights_window, 4)

        # ---------- Equipment Table ----------
        table_frame = tk.Frame(self, bg=self.BG_MAIN)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        tk.Label(
            table_frame,
            text="Equipment Inventory",
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
            font=self.FONT_SUBTITLE,
        ).pack(anchor="w", pady=(0, 5))

        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "Name", "Price", "Stock"),
            show="headings",
            height=20,
            style="Cyborg.Treeview",
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Price", text="Price")
        self.tree.heading("Stock", text="Stock")

        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Name", width=350, anchor="w")
        self.tree.column("Price", width=120, anchor="center")
        self.tree.column("Stock", width=120, anchor="center")

        self.tree.pack(fill="both", pady=5)

        self.load_equipment()

    # ---------- Style helpers ----------
    def _configure_treeview_style(self):
        # base dark style
        self.style.theme_use("default")
        self.style.configure(
            "Cyborg.Treeview",
            background="#050816",
            foreground="#E5F0FF",
            fieldbackground="#050816",
            bordercolor="#111827",
            rowheight=24,
        )
        self.style.map(
            "Cyborg.Treeview",
            background=[("selected", "#1F2937")],
            foreground=[("selected", "#00E5FF")],
        )
        self.style.configure(
            "Cyborg.Treeview.Heading",
            background="#0B1020",
            foreground="#E5F0FF",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map(
            "Cyborg.Treeview.Heading",
            background=[("active", "#111827")],
        )

    def add_hover_effect(self, widget, normal_bg, hover_bg):
        def on_enter(_):
            widget.config(bg=hover_bg)

        def on_leave(_):
            widget.config(bg=normal_bg)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _hover_color(self, base):
        if base == self.ACCENT:
            return self.ACCENT_DARK
        if base == self.SUCCESS:
            return "#059669"
        if base == self.DANGER:
            return "#DB295F"
        if base == self.WARNING:
            return "#B45309"
        if base == self.BG_SUBTLE:
            return "#111827"
        return base

    # ---------- Load Equipment ----------
    def load_equipment(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT equipment_id, name, price, stock FROM equipment")
        rows = cursor.fetchall()
        db.close()

        for row in rows:
            self.tree.insert("", tk.END, values=row)

    # ---------- ADD EQUIPMENT (SCROLLABLE) ----------
    def add_equipment_window(self):
        win = tk.Toplevel(self)
        win.title("Add Equipment - Cyborg")
        win.state("zoomed")
        win.config(bg=self.BG_MAIN)

        # ---- Scrollable container ----
        container = tk.Frame(win, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            container,
            bg=self.BG_MAIN,
            highlightthickness=0
        )
        v_scroll = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scrollable_frame = tk.Frame(canvas, bg=self.BG_MAIN)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", on_configure)

        # Optional: mouse wheel scrolling (Windows)
        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ---- Content goes into scrollable_frame ----
        tk.Label(
            scrollable_frame,
            text="Add Gym Equipment",
            font=("Segoe UI", 18, "bold"),
            bg=self.BG_MAIN,
            fg=self.ACCENT,
        ).pack(pady=15)

        fields = ["Name", "Brand", "Description", "Price", "Stock", "Image Path"]
        entries = {}

        def make_entry(label, with_browse=False):
            tk.Label(
                scrollable_frame,
                text=label,
                bg=self.BG_MAIN,
                fg=self.FG_TEXT,
                font=self.FONT_LABEL
            ).pack(anchor="w", padx=30)

            if with_browse:
                # Frame to hold entry + browse button
                container_row = tk.Frame(scrollable_frame, bg=self.BG_MAIN)
                container_row.pack(pady=3, padx=30, anchor="w", fill="x")

                e = tk.Entry(
                    container_row,
                    width=28,
                    bg=self.BG_ENTRY,
                    fg=self.FG_TEXT,
                    insertbackground=self.ACCENT,
                    relief="flat",
                )
                e.pack(side="left", ipady=4, pady=0)

                def browse_image():
                    file_path = filedialog.askopenfilename(
                        title="Select Image",
                        filetypes=[
                            ("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.webp"),
                            ("All Files", "*.*"),
                        ]
                    )
                    if file_path:
                        e.delete(0, tk.END)
                        e.insert(0, file_path)

                browse_btn = tk.Button(
                    container_row,
                    text="Browse",
                    command=browse_image,
                    bg=self.ACCENT,
                    fg=self.BG_MAIN,
                    relief="flat",
                    cursor="hand2",
                    font=("Segoe UI", 9, "bold"),
                )
                browse_btn.pack(side="left", padx=8)
                self.add_hover_effect(browse_btn, self.ACCENT, self.ACCENT_DARK)

                return e
            else:
                e = tk.Entry(
                    scrollable_frame,
                    width=35,
                    bg=self.BG_ENTRY,
                    fg=self.FG_TEXT,
                    insertbackground=self.ACCENT,
                    relief="flat",
                )
                e.pack(pady=3, padx=30, ipady=4)
                return e

        # Create normal entries first, and special one for Image Path
        for f in fields:
            if f == "Image Path":
                entries[f] = make_entry(f, with_browse=True)
            else:
                entries[f] = make_entry(f)

        tk.Label(
            scrollable_frame,
            text="Category",
            font=("Segoe UI", 12, "bold"),
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
        ).pack(pady=(15, 5), anchor="w", padx=30)

        category_var = tk.StringVar(value=CATEGORIES[0])
        cat_frame = tk.Frame(scrollable_frame, bg=self.BG_MAIN)
        cat_frame.pack(anchor="w", padx=30)
        for c in CATEGORIES:
            tk.Radiobutton(
                cat_frame,
                text=c,
                variable=category_var,
                value=c,
                bg=self.BG_MAIN,
                fg=self.FG_MUTED,
                selectcolor=self.BG_ENTRY,
                activebackground=self.BG_MAIN,
                activeforeground=self.ACCENT,
                font=("Segoe UI", 9),
            ).pack(anchor="w")

        tk.Label(
            scrollable_frame,
            text="Difficulty Level",
            font=("Segoe UI", 12, "bold"),
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
        ).pack(pady=(15, 5), anchor="w", padx=30)

        difficulty_var = tk.StringVar(value="Beginner")
        diff_frame = tk.Frame(scrollable_frame, bg=self.BG_MAIN)
        diff_frame.pack(anchor="w", padx=30)
        for lvl in ["Beginner", "Intermediate", "Advanced"]:
            tk.Radiobutton(
                diff_frame,
                text=lvl,
                variable=difficulty_var,
                value=lvl,
                bg=self.BG_MAIN,
                fg=self.FG_MUTED,
                selectcolor=self.BG_ENTRY,
                activebackground=self.BG_MAIN,
                activeforeground=self.ACCENT,
                font=("Segoe UI", 9),
            ).pack(anchor="w")

        def save():
            name = entries["Name"].get().strip()
            brand = entries["Brand"].get().strip()
            description = entries["Description"].get().strip()
            price = entries["Price"].get().strip()
            stock = entries["Stock"].get().strip()
            image_path = entries["Image Path"].get().strip()

            if not name or not price or not stock:
                messagebox.showerror("Error", "Name, Price, and Stock are required!")
                return

            try:
                price_val = float(price)
                stock_val = int(stock)
            except ValueError:
                messagebox.showerror("Error", "Price must be a number and Stock must be an integer")
                return

            category_id = get_category_id(category_var.get())
            difficulty = difficulty_var.get()

            db = connect_db()
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO equipment (name, brand, description, price, stock, category_id, image_path, difficulty)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (name, brand, description, price_val, stock_val, category_id, image_path, difficulty),
            )
            db.commit()
            db.close()

            messagebox.showinfo("Success", "Equipment added successfully")
            win.destroy()
            self.load_equipment()

        add_btn = tk.Button(
            scrollable_frame,
            text="Add Equipment",
            bg=self.SUCCESS,
            fg=self.BG_MAIN,
            font=self.FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            activebackground="#059669",
            activeforeground=self.BG_MAIN,
            command=save,
        )
        add_btn.pack(pady=20)
        self.add_hover_effect(add_btn, self.SUCCESS, "#059669")

    # ---------- UPDATE EQUIPMENT (SCROLLABLE) ----------
    def update_equipment_window(self):
        win = tk.Toplevel(self)
        win.title("Update Equipment - Cyborg")
        win.state("zoomed")
        win.config(bg=self.BG_MAIN)

        # ---- Scrollable container ----
        container = tk.Frame(win, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            container,
            bg=self.BG_MAIN,
            highlightthickness=0
        )
        v_scroll = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scrollable_frame = tk.Frame(canvas, bg=self.BG_MAIN)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", on_configure)

        # Optional mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ---- Content goes into scrollable_frame ----
        tk.Label(
            scrollable_frame,
            text="Update Equipment",
            font=("Segoe UI", 18, "bold"),
            bg=self.BG_MAIN,
            fg=self.ACCENT,
        ).pack(pady=10)

        tk.Label(
            scrollable_frame,
            text="Enter Equipment ID to Update",
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
            font=self.FONT_LABEL,
        ).pack(pady=5)
        id_row = tk.Frame(scrollable_frame, bg=self.BG_MAIN)
        id_row.pack(pady=5)
        id_entry = tk.Entry(
            id_row,
            width=18,
            bg=self.BG_ENTRY,
            fg=self.FG_TEXT,
            insertbackground=self.ACCENT,
            relief="flat",
        )
        id_entry.pack(side="left", padx=(0, 8), ipady=3)
        load_btn = tk.Button(
            id_row,
            text="Load Details",
            bg=self.ACCENT,
            fg=self.BG_MAIN,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
        )
        load_btn.pack(side="left")
        self.add_hover_effect(load_btn, self.ACCENT, self.ACCENT_DARK)

        fields = ["Name", "Brand", "Description", "Price", "Stock", "Image Path"]
        entries = {}

        def make_entry(label):
            tk.Label(
                scrollable_frame,
                text=label,
                bg=self.BG_MAIN,
                fg=self.FG_TEXT,
                font=self.FONT_LABEL
            ).pack(anchor="w", padx=30)
            e = tk.Entry(
                scrollable_frame,
                width=35,
                bg=self.BG_ENTRY,
                fg=self.FG_TEXT,
                insertbackground=self.ACCENT,
                relief="flat",
            )
            e.pack(pady=3, padx=30, ipady=4)
            return e

        for f in fields:
            entries[f] = make_entry(f)

        tk.Label(
            scrollable_frame,
            text="Category",
            font=("Segoe UI", 12, "bold"),
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
        ).pack(pady=(15, 5), anchor="w", padx=30)
        category_var = tk.StringVar(value=CATEGORIES[0])
        cat_frame = tk.Frame(scrollable_frame, bg=self.BG_MAIN)
        cat_frame.pack(anchor="w", padx=30)
        for c in CATEGORIES:
            tk.Radiobutton(
                cat_frame,
                text=c,
                variable=category_var,
                value=c,
                bg=self.BG_MAIN,
                fg=self.FG_MUTED,
                selectcolor=self.BG_ENTRY,
                activebackground=self.BG_MAIN,
                activeforeground=self.ACCENT,
                font=("Segoe UI", 9),
            ).pack(anchor="w")

        tk.Label(
            scrollable_frame,
            text="Difficulty Level",
            font=("Segoe UI", 12, "bold"),
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
        ).pack(pady=(15, 5), anchor="w", padx=30)
        difficulty_var = tk.StringVar(value="Beginner")
        diff_frame = tk.Frame(scrollable_frame, bg=self.BG_MAIN)
        diff_frame.pack(anchor="w", padx=30)
        for lvl in ["Beginner", "Intermediate", "Advanced"]:
            tk.Radiobutton(
                diff_frame,
                text=lvl,
                variable=difficulty_var,
                value=lvl,
                bg=self.BG_MAIN,
                fg=self.FG_MUTED,
                selectcolor=self.BG_ENTRY,
                activebackground=self.BG_MAIN,
                activeforeground=self.ACCENT,
                font=("Segoe UI", 9),
            ).pack(anchor="w")

        def load_equipment_details():
            eid = id_entry.get().strip()
            if not eid:
                messagebox.showerror("Error", "Equipment ID required")
                return

            try:
                db = connect_db()
                cur = db.cursor()
                cur.execute(
                    """
                    SELECT name, brand, description, price, stock, image_path, category_id, difficulty
                    FROM equipment
                    WHERE equipment_id=%s
                    """,
                    (eid,),
                )
                row = cur.fetchone()
                if not row:
                    db.close()
                    messagebox.showerror("Not Found", f"No equipment with ID {eid}")
                    return

                name, brand, description, price, stock, image_path, category_id, difficulty = row

                entries["Name"].delete(0, tk.END)
                entries["Name"].insert(0, name or "")

                entries["Brand"].delete(0, tk.END)
                entries["Brand"].insert(0, brand or "")

                entries["Description"].delete(0, tk.END)
                entries["Description"].insert(0, description or "")

                entries["Price"].delete(0, tk.END)
                entries["Price"].insert(0, str(price))

                entries["Stock"].delete(0, tk.END)
                entries["Stock"].insert(0, str(stock))

                entries["Image Path"].delete(0, tk.END)
                entries["Image Path"].insert(0, image_path or "")

                cat_name = None
                if category_id:
                    cur.execute(
                        "SELECT name FROM equipment_category WHERE category_id=%s",
                        (category_id,),
                    )
                    c = cur.fetchone()
                    if c and c[0] in CATEGORIES:
                        cat_name = c[0]
                category_var.set(cat_name or CATEGORIES[0])

                if difficulty in ["Beginner", "Intermediate", "Advanced"]:
                    difficulty_var.set(difficulty)
                else:
                    difficulty_var.set("Beginner")

                db.close()
            except mysql.connector.Error as err:
                messagebox.showerror("DB Error", str(err))

        load_btn.config(command=load_equipment_details)
        id_entry.bind("<Return>", lambda e: load_equipment_details())

        def update():
            eid = id_entry.get().strip()
            if not eid:
                messagebox.showerror("Error", "Equipment ID required")
                return

            name = entries["Name"].get().strip()
            brand = entries["Brand"].get().strip()
            description = entries["Description"].get().strip()
            price = entries["Price"].get().strip()
            stock = entries["Stock"].get().strip()
            image_path = entries["Image Path"].get().strip()

            if not name or not price or not stock:
                messagebox.showerror("Error", "Name, Price and Stock are required")
                return

            try:
                price_val = float(price)
                stock_val = int(stock)
            except ValueError:
                messagebox.showerror("Error", "Price must be a number and Stock must be an integer")
                return

            category_id = get_category_id(category_var.get())
            difficulty = difficulty_var.get()

            db = connect_db()
            cursor = db.cursor()
            cursor.execute(
                """
                UPDATE equipment
                SET name=%s, brand=%s, description=%s, price=%s, stock=%s,
                    category_id=%s, image_path=%s, difficulty=%s
                WHERE equipment_id=%s
                """,
                (name, brand, description, price_val, stock_val, category_id, image_path, difficulty, eid),
            )
            db.commit()
            db.close()

            messagebox.showinfo("Updated", "Equipment updated successfully")
            win.destroy()
            self.load_equipment()

        upd_btn = tk.Button(
            scrollable_frame,
            text="Update Equipment",
            bg=self.WARNING,
            fg=self.BG_MAIN,
            font=self.FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            activebackground="#B45309",
            activeforeground=self.BG_MAIN,
            command=update,
        )
        upd_btn.pack(pady=20)
        self.add_hover_effect(upd_btn, self.WARNING, "#B45309")

    # ---------- DELETE EQUIPMENT ----------
    def delete_equipment_window(self):
        win = tk.Toplevel(self)
        win.title("Delete Equipment - Cyborg")
        win.geometry("400x400")
        win.config(bg=self.BG_MAIN)

        tk.Label(
            win,
            text="Delete Equipment",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_MAIN,
            fg=self.DANGER,
        ).pack(pady=10)

        tk.Label(
            win,
            text="Enter Equipment ID to Delete",
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
            font=self.FONT_LABEL,
        ).pack(pady=5)
        id_entry = tk.Entry(
            win,
            width=20,
            bg=self.BG_ENTRY,
            fg=self.FG_TEXT,
            insertbackground=self.ACCENT,
            relief="flat",
        )
        id_entry.pack(pady=10, ipady=3)

        def delete():
            eid = id_entry.get().strip()
            if not eid:
                messagebox.showerror("Error", "Equipment ID required")
                return

            db = connect_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM equipment WHERE equipment_id=%s", (eid,))
            db.commit()
            db.close()

            messagebox.showinfo("Deleted", "Equipment deleted successfully")
            win.destroy()
            self.load_equipment()

        del_btn = tk.Button(
            win,
            text="Delete",
            bg=self.DANGER,
            fg=self.BG_MAIN,
            font=self.FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            activebackground="#DB295F",
            activeforeground=self.BG_MAIN,
            command=delete,
        )
        del_btn.pack(pady=10)
        self.add_hover_effect(del_btn, self.DANGER, "#DB295F")

    # ---------- CUSTOMERS MANAGEMENT ----------
    def open_customers_window(self):
        win = tk.Toplevel(self)
        win.title("Customer Management - Cyborg")
        win.geometry("1100x650")
        win.config(bg=self.BG_MAIN)

        ctrl = tk.Frame(win, bg=self.BG_MAIN)
        ctrl.pack(fill="x", padx=10, pady=5)

        title_lbl = tk.Label(
            ctrl,
            text="Customer Management",
            bg=self.BG_MAIN,
            fg=self.ACCENT,
            font=self.FONT_SUBTITLE,
        )
        title_lbl.pack(side="left")

        refresh_btn = tk.Button(
            ctrl,
            text="Refresh",
            bg=self.ACCENT,
            fg=self.BG_MAIN,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
        )
        refresh_btn.pack(side="right")
        self.add_hover_effect(refresh_btn, self.ACCENT, self.ACCENT_DARK)

        cols = ("ID", "Name", "Email", "Phone", "Login Count", "Total Spent", "Last Login")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=20, style="Cyborg.Treeview")
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=60, anchor="center")
        tree.column("Name", width=180, anchor="w")
        tree.column("Email", width=220, anchor="w")
        tree.column("Phone", width=120, anchor="center")
        tree.column("Login Count", width=120, anchor="center")
        tree.column("Total Spent", width=120, anchor="center")
        tree.column("Last Login", width=180, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def load_customers():
            for i in tree.get_children():
                tree.delete(i)
            try:
                db = connect_db()
                cur = db.cursor()
                cur.execute(
                    """
                    SELECT customer_id, full_name, email, COALESCE(phone,''),
                           COALESCE(login_count,0), COALESCE(total_spent,0), last_login
                    FROM customers
                    ORDER BY customer_id ASC
                    """
                )
                rows = cur.fetchall()
                db.close()
                for r in rows:
                    cid, name, email, phone, logins, spent, last_login = r
                    tree.insert(
                        "",
                        tk.END,
                        values=(
                            cid,
                            name,
                            email,
                            phone,
                            logins,
                            f"${float(spent):.2f}",
                            str(last_login) if last_login else "-",
                        ),
                    )
            except mysql.connector.Error as err:
                messagebox.showerror("DB Error", str(err))

        refresh_btn.config(command=load_customers)
        load_customers()

    # ---------- INSIGHTS DASHBOARD ----------
    def open_insights_window(self):
        win = tk.Toplevel(self)
        win.title("Insights Dashboard - FIT NZ (Cyborg)")
        win.geometry("1200x750")
        win.config(bg=self.BG_MAIN)

        container = tk.Frame(win, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        header_frame = tk.Frame(container, bg=self.BG_MAIN)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text="Insights Dashboard",
            bg=self.BG_MAIN,
            fg=self.ACCENT,
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        refresh_btn = tk.Button(
            header_frame,
            text="Refresh",
            bg=self.ACCENT,
            fg=self.BG_MAIN,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
        )
        refresh_btn.pack(side="right")
        self.add_hover_effect(refresh_btn, self.ACCENT, self.ACCENT_DARK)

        top_frame = tk.Frame(container, bg=self.BG_MAIN)
        top_frame.pack(fill="x", pady=(10, 5))

        bottom_frame = tk.Frame(container, bg=self.BG_MAIN)
        bottom_frame.pack(fill="both", expand=True)

        most_canvas = tk.Canvas(
            top_frame,
            width=560,
            height=260,
            bg=self.BG_CARD,
            highlightthickness=1,
            highlightbackground="#1F2937",
        )
        least_canvas = tk.Canvas(
            top_frame,
            width=560,
            height=260,
            bg=self.BG_CARD,
            highlightthickness=1,
            highlightbackground="#1F2937",
        )
        most_canvas.pack(side="left", padx=10, pady=5)
        least_canvas.pack(side="left", padx=10, pady=5)

        revenue_canvas = tk.Canvas(
            bottom_frame,
            width=1120,
            height=260,
            bg=self.BG_CARD,
            highlightthickness=1,
            highlightbackground="#1F2937",
        )
        revenue_canvas.pack(padx=10, pady=5)

        inv_frame = tk.Frame(bottom_frame, bg=self.BG_MAIN)
        inv_frame.pack(fill="both", expand=True, padx=10, pady=(5, 5))

        tk.Label(
            inv_frame,
            text="Low Stock (Top 10)",
            font=("Segoe UI", 12, "bold"),
            bg=self.BG_MAIN,
            fg=self.FG_TEXT,
        ).pack(anchor="w", pady=(0, 2))

        inv_tree = ttk.Treeview(
            inv_frame,
            columns=("ID", "Name", "Stock"),
            show="headings",
            height=8,
            style="Cyborg.Treeview",
        )
        for c in ("ID", "Name", "Stock"):
            inv_tree.heading(c, text=c)
        inv_tree.column("ID", width=80, anchor="center")
        inv_tree.column("Name", width=500, anchor="w")
        inv_tree.column("Stock", width=120, anchor="center")
        inv_tree.pack(fill="x", padx=2, pady=5)

        # ---------- Drawing helpers ----------
        def draw_bar_chart(canvas, title, data):
            canvas.delete("all")
            w = int(canvas["width"])
            h = int(canvas["height"])
            pad = 35

            canvas.create_text(
                pad,
                20,
                anchor="w",
                text=title,
                font=("Segoe UI", 12, "bold"),
                fill=self.FG_TEXT,
            )
            if not data:
                canvas.create_text(
                    w // 2,
                    h // 2,
                    text="No data",
                    font=("Segoe UI", 12, "italic"),
                    fill=self.FG_MUTED,
                )
                return
            labels = [d[0] for d in data]
            values = [max(0, float(d[1])) for d in data]
            max_val = max(values) if any(values) else 1.0
            bar_w = max(24, (w - pad * 2) // max(1, len(values)))
            base_y = h - pad

            for i, (label, val) in enumerate(zip(labels, values)):
                x0 = pad + i * bar_w + 8
                x1 = x0 + bar_w - 16
                bh = int((h - pad * 2) * (val / max_val))
                y1 = base_y
                y0 = y1 - bh
                canvas.create_rectangle(x0, y0, x1, y1, fill=self.ACCENT, outline="")
                short = label if len(label) <= 10 else label[:9] + "…"
                canvas.create_text(
                    (x0 + x1) // 2,
                    y1 + 10,
                    text=short,
                    anchor="n",
                    font=("Segoe UI", 8),
                    fill=self.FG_MUTED,
                )
                canvas.create_text(
                    (x0 + x1) // 2,
                    y0 - 6,
                    text=f"{val:.0f}",
                    anchor="s",
                    font=("Segoe UI", 8),
                    fill=self.FG_TEXT,
                )

        def draw_line_chart(canvas, title, data_points):
            canvas.delete("all")
            w = int(canvas["width"])
            h = int(canvas["height"])
            pad = 45

            canvas.create_text(
                pad,
                20,
                anchor="w",
                text=title,
                font=("Segoe UI", 12, "bold"),
                fill=self.FG_TEXT,
            )
            if not data_points:
                canvas.create_text(
                    w // 2,
                    h // 2,
                    text="No data",
                    font=("Segoe UI", 12, "italic"),
                    fill=self.FG_MUTED,
                )
                return
            labels = [d[0] for d in data_points]
            values = [max(0.0, float(d[1])) for d in data_points]
            max_val = max(values) if any(values) else 1.0

            # Axes
            canvas.create_line(pad, h - pad, w - pad, h - pad, fill="#374151")
            canvas.create_line(pad, h - pad, pad, pad, fill="#374151")

            n = len(values)
            if n == 1:
                xs = [pad + (w - 2 * pad) // 2]
            else:
                xs = [pad + i * (w - 2 * pad) // (n - 1) for i in range(n)]
            ys = [h - pad - int((h - 2 * pad) * (v / max_val)) for v in values]

            # Line & points
            for i in range(1, n):
                canvas.create_line(xs[i - 1], ys[i - 1], xs[i], ys[i], fill=self.SUCCESS, width=2)
            for x, y, v in zip(xs, ys, values):
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=self.SUCCESS, outline="")
                canvas.create_text(x, y - 8, text=f"{v:.0f}", font=("Segoe UI", 8), fill=self.FG_TEXT)

            # Labels
            for x, lab in zip(xs, labels):
                canvas.create_text(
                    x,
                    h - pad + 12,
                    text=str(lab),
                    anchor="n",
                    font=("Segoe UI", 8),
                    fill=self.FG_MUTED,
                )

        def refresh():
            # Most sold
            try:
                most = get_most_sold_equipment(5)
                most_pairs = [(name, qty) for (_eid, name, qty) in most]
            except Exception:
                most_pairs = []
            draw_bar_chart(most_canvas, "Top 5 Most Sold Equipment", most_pairs)

            # Least sold
            try:
                least = get_least_sold_equipment(5)
                least_pairs = [(name, qty) for (_eid, name, qty) in least]
            except Exception:
                least_pairs = []
            draw_bar_chart(least_canvas, "Top 5 Least Sold Equipment", least_pairs)

            # Low inventory
            for i in inv_tree.get_children():
                inv_tree.delete(i)
            try:
                db = connect_db()
                cur = db.cursor()
                cur.execute("SELECT equipment_id, name, stock FROM equipment ORDER BY stock ASC LIMIT 10")
                rows = cur.fetchall()
                db.close()
                for r in rows:
                    inv_tree.insert("", tk.END, values=r)
            except Exception:
                pass

            # Revenue line chart
            try:
                db = connect_db()
                cur = db.cursor()
                cur.execute(
                    """
                    SELECT DATE(order_date) as d, SUM(total_amount) as total
                    FROM orders
                    GROUP BY d
                    ORDER BY d ASC
                    LIMIT 7
                    """
                )
                rows = cur.fetchall()
                db.close()
                data_points = [(str(d), float(t or 0)) for (d, t) in rows]
            except Exception:
                data_points = []

            draw_line_chart(revenue_canvas, "Revenue (Last up to 7 Days)", data_points)

        refresh_btn.config(command=refresh)
        refresh()


if __name__ == "__main__":
    app = AdminPanel()
    app.mainloop()
