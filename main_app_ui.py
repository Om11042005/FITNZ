# File: FITNZ/main_app_ui.py
import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from ttkbootstrap.scrolled import ScrolledFrame  # <-- Correct import
from . import database as db
from .admin_ui import AdminPage
from .customer_ui import CartPage, MembershipPage
from PIL import Image, ImageTk, UnidentifiedImageError, ImageDraw
import os
import shutil
from tkinter import filedialog

# --- HELPER FUNCTION (No changes) ---
def get_product_image_path(product_name):
    """
    Checks if an image exists locally in 'FITNZ/assets' with ANY common extension.
    Returns the local path if found, otherwise returns None.
    """
    assets_dir = os.path.join('FITNZ', 'assets')
    # Base filename without extension
    safe_basename = "".join(c for c in product_name.lower() if c.isalnum() or c == ' ').replace(' ', '_')
    
    os.makedirs(assets_dir, exist_ok=True)
    
    # Check for multiple extensions
    supported_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    
    for ext in supported_extensions:
        local_path = os.path.join(assets_dir, safe_basename + ext)
        if os.path.exists(local_path):
            try:
                # Check if the file is a valid image
                with Image.open(local_path) as img:
                    img.verify()
                return local_path # It's valid, return the path
            except (UnidentifiedImageError, IOError):
                print(f"File at {local_path} is corrupt. Please replace it.")
                return None # File is corrupt
                
    return None # No file found with any supported extension
# --- END HELPER FUNCTION ---


class MainAppPage(ttk.Frame):
    def __init__(self, parent, controller, logged_in_user):
        super().__init__(parent)
        self.controller = controller
        self.logged_in_user = logged_in_user
        self.cart = []
        
        self.product_images_list = [] 
        try:
            # Create default placeholder images
            img_default = Image.new('RGB', (150, 150), color = '#333333')
            self.default_photo_grid = ImageTk.PhotoImage(img_default) # For grid
            img_default_small = Image.new('RGB', (30, 30), color = '#333333')
            self.default_photo_tree = ImageTk.PhotoImage(img_default_small) # For treeview
        except Exception:
            self.default_photo_grid = None
            self.default_photo_tree = None
        
        self.new_product_image_path = None
        
        if self.logged_in_user.role == "Customer":
            self.build_customer_ui()
        else:
            self.build_staff_ui()

    # -----------------------------------------------------------------
    # Staff UI
    # -----------------------------------------------------------------
    def build_staff_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Top navigation bar with professional styling
        top_bar = ttk.Frame(self, padding=(15, 15, 15, 10), bootstyle="secondary")
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)
        
        # Left side - Action buttons
        left_actions = ttk.Frame(top_bar)
        left_actions.grid(row=0, column=0, sticky="w")
        
        if self.logged_in_user.role in ["Developer", "Manager", "Owner"]:
            admin_btn = ttk.Button(
                left_actions, 
                text="⚙️ Admin Panel", 
                bootstyle="info", 
                command=self.open_admin_panel,
                width=15
            )
            admin_btn.pack(side="left", padx=(0, 10))
        
        # Right side - User info and logout
        right_actions = ttk.Frame(top_bar)
        right_actions.grid(row=0, column=2, sticky="e")
        
        if self.logged_in_user.role == "Employee":
            user_info = f"Welcome, {self.logged_in_user.name}!"
        else:
            user_info = f"{self.logged_in_user.name} ({self.logged_in_user.role})"
        
        ttk.Label(
            right_actions, 
            text=user_info, 
            font=("Segoe UI", 11, "bold"), 
            bootstyle="inverse-secondary"
        ).pack(side="left", padx=(0, 15))
        
        logout_btn = ttk.Button(
            right_actions, 
            text="Logout", 
            command=self.controller.show_login_page, 
            bootstyle="danger-outline",
            width=12
        )
        logout_btn.pack(side="left")
        
        # Main content area with split panes
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Left pane - Product management
        left_pane = ttk.Frame(main_pane, padding=10)
        main_pane.add(left_pane, weight=3)
        left_pane.grid_rowconfigure(0, weight=1)
        left_pane.grid_columnconfigure(0, weight=1)
        
        # Right pane - Customer/Order management
        right_pane = ttk.Frame(main_pane, padding=10)
        main_pane.add(right_pane, weight=2)
        right_pane.grid_rowconfigure(0, weight=1)
        right_pane.grid_columnconfigure(0, weight=1)

        # Product inventory frame
        products_frame = ttk.Labelframe(
            left_pane, 
            text="📦 Product Inventory & Stock Management", 
            padding=15, 
            bootstyle="info"
        )
        products_frame.grid(row=0, column=0, sticky="nsew")
        products_frame.grid_rowconfigure(0, weight=1)
        products_frame.grid_columnconfigure(0, weight=1)
        
        # Product treeview with improved styling
        tree_frame = ttk.Frame(products_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        cols = ("id", "name", "price", "stock")
        self.product_tree = ttk.Treeview(
            tree_frame, 
            columns=cols, 
            show="tree headings", 
            bootstyle="primary",
            selectmode="browse"
        )
        
        # Configure tree columns
        self.product_tree.heading("#0", text="Image", anchor="center")
        self.product_tree.column("#0", width=50, anchor="center", stretch=False)
        self.product_tree.heading("id", text="Product ID", anchor="center")
        self.product_tree.column("id", width=120, anchor="center", stretch=False)
        self.product_tree.heading("name", text="Product Name", anchor="w")
        self.product_tree.column("name", width=250, anchor="w", stretch=True)
        self.product_tree.heading("price", text="Price", anchor="e")
        self.product_tree.column("price", width=120, anchor="e", stretch=False)
        self.product_tree.heading("stock", text="Stock", anchor="e")
        self.product_tree.column("stock", width=100, anchor="e", stretch=False)
        
        self.product_tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, 
            orient="vertical", 
            command=self.product_tree.yview,
            bootstyle="secondary-round"
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.load_products_to_treeview()
        
        # Action notebook for product management tabs
        action_notebook = ttk.Notebook(products_frame, bootstyle="primary")
        action_notebook.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        
        # Add Stock Tab
        stock_tab = ttk.Frame(action_notebook, padding=15)
        action_notebook.add(stock_tab, text="➕ Add Stock")
        
        self.selected_product_label = ttk.Label(
            stock_tab, 
            text="Selected: None", 
            font=("Segoe UI", 10, "bold"), 
            bootstyle="secondary"
        )
        self.selected_product_label.pack(fill="x", pady=(0, 15))
        
        stock_input_frame = ttk.Frame(stock_tab)
        stock_input_frame.pack(fill="x")
        stock_input_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(
            stock_tab, 
            text="Quantity to Add:", 
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(0, 8))
        
        entry_btn_frame = ttk.Frame(stock_tab)
        entry_btn_frame.pack(fill="x")
        entry_btn_frame.grid_columnconfigure(0, weight=1)
        
        self.stock_entry = ttk.Entry(
            entry_btn_frame, 
            font=("Segoe UI", 11)
        )
        self.stock_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=6)
        self.stock_entry.bind('<Return>', lambda e: self.add_stock())
        
        ttk.Button(
            entry_btn_frame, 
            text="Add Stock", 
            command=self.add_stock, 
            bootstyle="success",
            width=15
        ).grid(row=0, column=1, sticky="ew")

        if self.logged_in_user.role in ["Manager", "Developer", "Owner"]:
            # Add New Product Tab
            add_tab = ttk.Frame(action_notebook, padding=15)
            action_notebook.add(add_tab, text="➕ Add Product")
            add_tab.grid_columnconfigure(1, weight=1)
            
            fields = [
                ("Product ID:", "add_id_entry"),
                ("Product Name:", "add_name_entry"),
                ("Price ($):", "add_price_entry"),
                ("Initial Stock:", "add_stock_entry")
            ]
            
            for i, (label_text, attr_name) in enumerate(fields):
                ttk.Label(
                    add_tab, 
                    text=label_text, 
                    font=("Segoe UI", 10, "bold")
                ).grid(row=i, column=0, sticky="w", padx=(0, 15), pady=8)
                
                entry = ttk.Entry(add_tab, font=("Segoe UI", 10))
                entry.grid(row=i, column=1, sticky="ew", pady=8, ipady=6)
                setattr(self, attr_name, entry)
            
            # Image selection
            image_frame = ttk.Frame(add_tab)
            image_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)
            image_frame.grid_columnconfigure(1, weight=1)
            
            ttk.Label(
                image_frame, 
                text="Product Image:", 
                font=("Segoe UI", 10, "bold")
            ).grid(row=0, column=0, sticky="w", padx=(0, 15))
            
            self.add_image_label = ttk.Label(
                image_frame, 
                text="No file selected.", 
                bootstyle="secondary",
                font=("Segoe UI", 9)
            )
            self.add_image_label.grid(row=0, column=1, sticky="w", padx=(0, 10))
            
            ttk.Button(
                image_frame, 
                text="Browse...", 
                command=self.browse_for_image, 
                bootstyle="info-outline",
                width=12
            ).grid(row=0, column=2, sticky="e")
            
            # Add button
            add_btn = ttk.Button(
                add_tab, 
                text="➕ Add New Product", 
                command=self.add_product, 
                bootstyle="success",
                width=25
            )
            add_btn.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(15, 0), ipady=8)

            # Delete Product Tab
            delete_tab = ttk.Frame(action_notebook, padding=20)
            action_notebook.add(delete_tab, text="🗑️ Delete Product")
            
            ttk.Label(
                delete_tab, 
                text="Select a product from the list above to delete.", 
                font=("Segoe UI", 10),
                bootstyle="secondary"
            ).pack(pady=(10, 15))
            
            warning_frame = ttk.Labelframe(
                delete_tab, 
                text="⚠️ Warning", 
                padding=15,
                bootstyle="danger"
            )
            warning_frame.pack(fill="x", pady=(0, 15))
            
            ttk.Label(
                warning_frame, 
                text="This action cannot be undone. Deleting a product will remove it from ALL past sales records.", 
                wraplength=450, 
                justify="left",
                font=("Segoe UI", 9),
                bootstyle="inverse-danger"
            ).pack()
            
            ttk.Button(
                delete_tab, 
                text="🗑️ Delete Selected Product", 
                command=self.delete_product, 
                bootstyle="danger",
                width=25
            ).pack(pady=(10, 0), ipady=8)
        
        self.product_tree.bind("<<TreeviewSelect>>", self.on_product_select_staff)

        # Right notebook for management tabs
        right_notebook = ttk.Notebook(right_pane, bootstyle="primary")
        right_notebook.grid(row=0, column=0, sticky="nsew")
        
        if self.logged_in_user.role in ["Developer", "Manager", "Owner"]:
            # Customers Tab
            customers_tab = ttk.Frame(right_notebook, padding=10)
            right_notebook.add(customers_tab, text="👥 Customers")
            
            cust_frame = ttk.Labelframe(
                customers_tab, 
                text="Customer List", 
                padding=15, 
                bootstyle="info"
            )
            cust_frame.pack(expand=True, fill="both")
            cust_frame.grid_rowconfigure(0, weight=1)
            cust_frame.grid_columnconfigure(0, weight=1)
            
            # Customer treeview
            cust_tree_frame = ttk.Frame(cust_frame)
            cust_tree_frame.grid(row=0, column=0, sticky="nsew")
            cust_tree_frame.grid_rowconfigure(0, weight=1)
            cust_tree_frame.grid_columnconfigure(0, weight=1)
            
            self.customer_tree = ttk.Treeview(
                cust_tree_frame, 
                columns=("customer",), 
                show="headings", 
                bootstyle="primary",
                selectmode="browse"
            )
            self.customer_tree.heading("customer", text="Customer Information")
            self.customer_tree.column("customer", anchor="w", width=300)
            self.customer_tree.grid(row=0, column=0, sticky="nsew")
            
            cust_scroll = ttk.Scrollbar(
                cust_tree_frame, 
                orient="vertical", 
                command=self.customer_tree.yview,
                bootstyle="secondary-round"
            )
            cust_scroll.grid(row=0, column=1, sticky="ns")
            self.customer_tree.configure(yscrollcommand=cust_scroll.set)
            
            # Customer actions
            cust_actions = ttk.Frame(cust_frame)
            cust_actions.grid(row=0, column=1, sticky="ns", padx=(10, 0))
            
            ttk.Button(
                cust_actions, 
                text="View Details", 
                command=self.view_customer_details, 
                bootstyle="info-outline",
                width=15
            ).pack(pady=5)
            
            self.load_customers()
            
            # Orders Tab
            orders_tab = ttk.Frame(right_notebook, padding=10)
            right_notebook.add(orders_tab, text="📦 Recent Orders")
            
            order_frame = ttk.Labelframe(
                orders_tab, 
                text="All Sales", 
                padding=15, 
                bootstyle="success"
            )
            order_frame.pack(expand=True, fill="both")
            order_frame.grid_rowconfigure(0, weight=1)
            order_frame.grid_columnconfigure(0, weight=1)
            
            # Orders treeview
            order_tree_frame = ttk.Frame(order_frame)
            order_tree_frame.grid(row=0, column=0, sticky="nsew")
            order_tree_frame.grid_rowconfigure(0, weight=1)
            order_tree_frame.grid_columnconfigure(0, weight=1)
            
            order_cols = ("id", "cust", "del_date", "total")
            self.order_tree = ttk.Treeview(
                order_tree_frame, 
                columns=order_cols, 
                show="headings", 
                bootstyle="primary",
                selectmode="browse"
            )
            
            self.order_tree.heading("id", text="Order ID")
            self.order_tree.column("id", width=80, stretch=False, anchor="center")
            self.order_tree.heading("cust", text="Customer Name")
            self.order_tree.column("cust", width=150, anchor="w")
            self.order_tree.heading("del_date", text="Delivery Date")
            self.order_tree.column("del_date", width=120, anchor="center")
            self.order_tree.heading("total", text="Total Amount")
            self.order_tree.column("total", width=120, stretch=False, anchor="e")
            
            self.order_tree.grid(row=0, column=0, sticky="nsew")
            
            order_scroll = ttk.Scrollbar(
                order_tree_frame, 
                orient="vertical", 
                command=self.order_tree.yview,
                bootstyle="secondary-round"
            )
            order_scroll.grid(row=0, column=1, sticky="ns")
            self.order_tree.configure(yscrollcommand=order_scroll.set)
            
            # Order actions
            order_actions = ttk.Frame(order_frame)
            order_actions.grid(row=0, column=1, sticky="ns", padx=(10, 0))
            
            ttk.Button(
                order_actions, 
                text="View Details", 
                command=self.view_order_details, 
                bootstyle="info-outline",
                width=15
            ).pack(pady=5)
            
            self.load_orders()
        else:
            # Employee welcome tab
            welcome_tab = ttk.Frame(right_notebook, padding=30)
            right_notebook.add(welcome_tab, text="ℹ️ Information")
            
            info_frame = ttk.Labelframe(
                welcome_tab, 
                text="Stock Management", 
                padding=20,
                bootstyle="primary"
            )
            info_frame.pack(expand=True, fill="both")
            
            ttk.Label(
                info_frame, 
                text="Stock Management", 
                font=("Segoe UI", 18, "bold"), 
                bootstyle="primary"
            ).pack(pady=(10, 20))
            
            ttk.Label(
                info_frame, 
                text="Use the panel on the left to:\n\n• Browse all products in inventory\n• Select a product to manage\n• Add new stock quantities", 
                font=("Segoe UI", 11),
                justify="left"
            ).pack(pady=10)

    # -----------------------------------------------------------------
    # CUSTOMER UI
    # -----------------------------------------------------------------
    def build_customer_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Top bar for customer
        top_bar = ttk.Frame(self, padding=(15, 15, 15, 10), bootstyle="primary")
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)
        
        ttk.Label(
            top_bar, 
            text="🛒 Shop Our Products", 
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-primary"
        ).grid(row=0, column=0, sticky="w")
        
        ttk.Button(
            top_bar, 
            text="Logout", 
            command=self.controller.show_login_page, 
            bootstyle="danger-outline",
            width=12
        ).grid(row=0, column=2, sticky="e")
        
        # Products section
        products_frame = ttk.Labelframe(
            self, 
            text="🏋️ Our Products", 
            padding=15, 
            bootstyle="info"
        )
        products_frame.grid(row=1, column=0, padx=(15, 10), pady=(0, 15), sticky="nsew")
        products_frame.grid_rowconfigure(0, weight=1)
        products_frame.grid_columnconfigure(0, weight=1)

        # Scrolled frame for products grid
        self.scroll_frame = ScrolledFrame(products_frame, autohide=True, bootstyle="light")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew")
        
        # Load product grid
        self.load_product_grid(self.scroll_frame)
        
        # Right sidebar
        right_pane = ttk.Frame(self, padding=15)
        right_pane.grid(row=1, column=1, padx=(0, 15), pady=(0, 15), sticky="nsew")
        
        # Welcome/Info card
        self.info_frame = ttk.Labelframe(
            right_pane, 
            text=f"👋 Welcome, {self.logged_in_user.get_name()}!", 
            padding=20, 
            bootstyle="primary"
        )
        self.info_frame.pack(fill="x", pady=(0, 15))
        
        self.membership_label = ttk.Label(
            self.info_frame, 
            font=("Segoe UI", 11, "bold")
        )
        self.membership_label.pack(anchor="w", pady=(0, 5))
        
        self.points_label = ttk.Label(
            self.info_frame, 
            font=("Segoe UI", 11)
        )
        self.points_label.pack(anchor="w", pady=(0, 15))
        
        self.update_customer_info()
        
        ttk.Button(
            self.info_frame, 
            text="⭐ Manage Membership", 
            command=self.open_membership, 
            bootstyle="info-outline",
            width=20
        ).pack(fill="x", ipady=6)
        
        # Shopping actions
        actions_frame = ttk.Labelframe(
            right_pane, 
            text="🛍️ Shopping", 
            padding=20, 
            bootstyle="info"
        )
        actions_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Button(
            actions_frame, 
            text="🛒 View Cart", 
            command=self.open_cart, 
            bootstyle="success",
            width=20
        ).pack(fill="x", ipady=8, pady=(0, 10))
        
        ttk.Button(
            actions_frame, 
            text="📦 My Orders", 
            command=self.open_order_history, 
            bootstyle="primary-outline",
            width=20
        ).pack(fill='x', ipady=8)

    # ---
    # Functions
    # ---

    def on_product_select_staff(self, event):
        selected_item = self.product_tree.focus()
        if selected_item:
            item_values = self.product_tree.item(selected_item, "values")
            self.selected_product_label.config(text=f"Selected: {item_values[1]}")

    def load_products_to_treeview(self):
        self.product_images_list.clear() 
        self.product_tree.tag_configure('outofstock', foreground='#E55934')
        for item in self.product_tree.get_children(): self.product_tree.delete(item)
        
        for p in db.get_all_products():
            photo = self.default_photo_tree
            image_path = get_product_image_path(p.name)
            
            if image_path:
                try:
                    img = Image.open(image_path)
                    img = img.resize((30, 30), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.product_images_list.append(photo)
                except Exception as e:
                    print(f"Failed to load image {p.name}: {e}")
                    photo = self.default_photo_tree
                    
            tags = ('outofstock',) if p.stock == 0 else ()
            self.product_tree.insert(
                "", tk.END, iid=p.product_id, image=photo, text="",
                values=(p.product_id, p.name, f"${p.price:.2f}", p.stock), 
                tags=tags
            )

    def load_product_grid(self, parent_frame):
        """Load products in a responsive grid layout with improved styling."""
        self.product_images_list.clear()
        for widget in parent_frame.winfo_children():
            widget.destroy()
            
        products = db.get_all_products()
        MAX_COLS = 3
        
        if not products:
            empty_label = ttk.Label(
                parent_frame, 
                text="No products available at this time.", 
                font=("Segoe UI", 12),
                bootstyle="secondary"
            )
            empty_label.pack(pady=50)
            return
        
        for i, p in enumerate(products):
            row = i // MAX_COLS
            col = i % MAX_COLS
            
            # Product card with improved styling
            card = ttk.Labelframe(
                parent_frame, 
                text=p.name, 
                padding=15,
                bootstyle="light"
            )
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
            card.grid_rowconfigure(0, weight=0)
            card.grid_rowconfigure(1, weight=1)
            card.grid_rowconfigure(2, weight=0)
            card.grid_columnconfigure(0, weight=1)

            # Product image
            photo = self.default_photo_grid
            image_path = get_product_image_path(p.name)
            if image_path:
                try:
                    img = Image.open(image_path)
                    img = img.resize((180, 180), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.product_images_list.append(photo)
                except Exception:
                    photo = self.default_photo_grid
            
            img_label = ttk.Label(card, image=photo, anchor="center")
            img_label.grid(row=0, column=0, pady=(0, 10))
            
            # Product info frame
            info_frame = ttk.Frame(card)
            info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
            info_frame.grid_columnconfigure((0, 1), weight=1)
            
            # Price with better styling
            price_label = ttk.Label(
                info_frame, 
                text=f"${p.price:.2f}", 
                font=("Segoe UI", 14, "bold"),
                bootstyle="primary"
            )
            price_label.grid(row=0, column=0, sticky="w")
            
            # Stock status with better styling
            if p.stock > 0:
                stock_label_text = f"In Stock ({p.stock})"
                stock_style = "success"
            else:
                stock_label_text = "Out of Stock"
                stock_style = "danger"
            
            stock_label = ttk.Label(
                info_frame, 
                text=stock_label_text, 
                bootstyle=stock_style,
                font=("Segoe UI", 9, "bold")
            )
            stock_label.grid(row=0, column=1, sticky="e")
            
            # Add to cart button
            add_btn = ttk.Button(
                card, 
                text="➕ Add to Cart", 
                command=lambda p=p: self.add_to_cart(p),
                bootstyle="success",
                width=20
            )
            add_btn.grid(row=2, column=0, sticky="ew", pady=(5, 0), ipady=6)
            
            if p.stock == 0:
                add_btn.config(state="disabled", bootstyle="secondary")
                stock_label.config(text="❌ Out of Stock", bootstyle="danger")
        
        # Configure grid columns for responsive layout
        for col in range(MAX_COLS):
            parent_frame.grid_columnconfigure(col, weight=1, uniform="cols")

    def browse_for_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Product Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")]
        )
        
        if file_path:
            self.new_product_image_path = file_path
            filename = os.path.basename(file_path)
            self.add_image_label.config(text=filename)
        else:
            self.new_product_image_path = None
            self.add_image_label.config(text="No file selected.")

    def add_stock(self):
        """Add stock to the selected product with validation."""
        selected_item = self.product_tree.focus()
        if not selected_item: 
            Messagebox.show_warning(
                "Please select a product from the list first.", 
                "No Product Selected", 
                parent=self
            )
            return
        
        stock_input = self.stock_entry.get().strip()
        if not stock_input:
            Messagebox.show_warning(
                "Please enter a quantity to add.", 
                "Empty Input", 
                parent=self
            )
            self.stock_entry.focus_set()
            return
        
        try:
            quantity_to_add = int(stock_input)
            if quantity_to_add <= 0:
                Messagebox.show_error(
                    "Quantity must be a positive number greater than zero.", 
                    "Invalid Quantity", 
                    parent=self
                )
                self.stock_entry.focus_set()
                return
            
            if quantity_to_add > 10000:
                Messagebox.show_warning(
                    "That's a very large quantity. Please verify the number is correct.", 
                    "Large Quantity Warning", 
                    parent=self
                )
            
            product_id = self.product_tree.item(selected_item, "values")[0]
            product_name = self.product_tree.item(selected_item, "values")[1]
            current_product = db.get_product_by_id(product_id)
            
            if not current_product:
                Messagebox.show_error(
                    "Could not find the selected product in the database.", 
                    "Product Not Found", 
                    parent=self
                )
                return
            
            new_quantity = current_product.stock + quantity_to_add
            
            if db.update_product_stock(product_id, new_quantity):
                Messagebox.show_info(
                    f"Successfully added {quantity_to_add} units to {product_name}.\nNew stock level: {new_quantity}", 
                    "Stock Updated", 
                    parent=self
                )
                self.load_products_to_treeview()
                self.stock_entry.delete(0, "end")
                self.selected_product_label.config(text="Selected: None")
                self.stock_entry.focus_set()
            else:
                Messagebox.show_error(
                    "Failed to update stock in the database. Please try again.", 
                    "Update Failed", 
                    parent=self
                )
        except ValueError:
            Messagebox.show_error(
                "Please enter a valid whole number (e.g., 10, 50, 100).", 
                "Invalid Input", 
                parent=self
            )
            self.stock_entry.focus_set()

    def add_product(self):
        """Add a new product with comprehensive validation."""
        prod_id = self.add_id_entry.get().strip()
        name = self.add_name_entry.get().strip()
        price_str = self.add_price_entry.get().strip()
        stock_str = self.add_stock_entry.get().strip()
        
        # Validate all fields are filled
        if not prod_id:
            Messagebox.show_error("Please enter a Product ID.", "Missing Field", parent=self)
            self.add_id_entry.focus_set()
            return
        
        if not name:
            Messagebox.show_error("Please enter a product name.", "Missing Field", parent=self)
            self.add_name_entry.focus_set()
            return
        
        if not price_str:
            Messagebox.show_error("Please enter a price.", "Missing Field", parent=self)
            self.add_price_entry.focus_set()
            return
        
        if not stock_str:
            Messagebox.show_error("Please enter initial stock quantity.", "Missing Field", parent=self)
            self.add_stock_entry.focus_set()
            return
        
        # Validate image
        if not self.new_product_image_path:
            Messagebox.show_error("Please select an image for the product.", "Missing Image", parent=self)
            return
        
        # Validate Product ID format
        if len(prod_id) < 2:
            Messagebox.show_error("Product ID must be at least 2 characters long.", "Invalid Product ID", parent=self)
            self.add_id_entry.focus_set()
            return
        
        # Validate price
        try:
            price = float(price_str)
            if price <= 0:
                Messagebox.show_error("Price must be greater than zero.", "Invalid Price", parent=self)
                self.add_price_entry.focus_set()
                return
            if price > 99999:
                Messagebox.show_warning("Price seems unusually high. Please verify.", "Price Warning", parent=self)
        except ValueError:
            Messagebox.show_error("Price must be a valid number (e.g., 29.99).", "Invalid Price Format", parent=self)
            self.add_price_entry.focus_set()
            return
        
        # Validate stock
        try:
            stock = int(stock_str)
            if stock < 0:
                Messagebox.show_error("Stock quantity cannot be negative.", "Invalid Stock", parent=self)
                self.add_stock_entry.focus_set()
                return
        except ValueError:
            Messagebox.show_error("Stock must be a valid whole number (e.g., 50).", "Invalid Stock Format", parent=self)
            self.add_stock_entry.focus_set()
            return

        # Copy image file
        try:
            assets_dir = os.path.join('FITNZ', 'assets')
            os.makedirs(assets_dir, exist_ok=True)
            safe_basename = "".join(c for c in name.lower() if c.isalnum() or c == ' ').replace(' ', '_')
            file_extension = os.path.splitext(self.new_product_image_path)[1]
            destination_filename = safe_basename + file_extension
            destination_path = os.path.join(assets_dir, destination_filename)
            
            # Check if file already exists
            if os.path.exists(destination_path):
                if not Messagebox.yesno(
                    f"An image file with this name already exists.\nOverwrite it?",
                    "File Exists",
                    parent=self
                ):
                    return
            
            shutil.copy(self.new_product_image_path, destination_path)
            
        except Exception as e:
            Messagebox.show_error(
                f"Failed to save product image:\n{str(e)}", 
                "Image Save Error", 
                parent=self
            )
            return
        
        # Add product to database
        if db.add_product(prod_id, name, price, stock):
            Messagebox.show_info(
                f"Product '{name}' added successfully!\nProduct ID: {prod_id}\nPrice: ${price:.2f}\nStock: {stock}", 
                "Product Added", 
                parent=self
            )
            self.load_products_to_treeview()
            
            # Clear form
            self.add_id_entry.delete(0, "end")
            self.add_name_entry.delete(0, "end")
            self.add_price_entry.delete(0, "end")
            self.add_stock_entry.delete(0, "end")
            self.new_product_image_path = None
            self.add_image_label.config(text="No file selected.")
        else:
            Messagebox.show_error(
                f"Failed to add product. The Product ID '{prod_id}' may already exist in the database.", 
                "Add Failed", 
                parent=self
            )
            # Clean up copied image if product addition failed
            if os.path.exists(destination_path):
                try:
                    os.remove(destination_path)
                except:
                    pass

    def delete_product(self):
        selected_item = self.product_tree.focus()
        if not selected_item:
            Messagebox.show_warning("Please select a product to delete.", "No Selection", parent=self)
            return
            
        product_id = self.product_tree.item(selected_item, "values")[0]
        product_name = self.product_tree.item(selected_item, "values")[1]

        if not Messagebox.yesno(f"Are you sure you want to permanently delete '{product_name}'?\n\nThis action cannot be undone and will remove it from all past sales records.", "Confirm Deletion", parent=self):
            return
        
        try:
            image_path = get_product_image_path(product_name)
            if image_path:
                os.remove(image_path)
                print(f"Deleted image: {image_path}")
        except Exception as e:
            print(f"Could not delete image: {e}")
            
        if db.delete_product(product_id):
            Messagebox.show_info(f"'{product_name}' was deleted successfully.", "Success", parent=self)
            self.load_products_to_treeview()
        else:
            Messagebox.show_error("Failed to delete product.", "Error", parent=self)

    def view_customer_details(self):
        selected = self.customer_tree.focus()
        if not selected: Messagebox.show_warning("Please select a customer.", "No Selection", parent=self); return
        try:
            customer_id = self.customer_tree.item(selected, "values")[0].split(",")[0].split(": ")[1]
            customer = db.get_user_by_id(customer_id)
            if customer: CustomerDetailsPage(self, customer)
        except IndexError:
            Messagebox.show_error("Could not parse customer ID.", "Error", parent=self)

    def view_order_details(self):
        selected = self.order_tree.focus()
        if not selected: Messagebox.show_warning("Please select an order.", "No Selection", parent=self); return
        sale_id = self.order_tree.item(selected, "values")[0]
        OrderDetailsPage(self, sale_id)
        
    def open_order_history(self):
        if hasattr(self.logged_in_user, '_customer_id'):
            OrderHistoryPage(self, self.logged_in_user._customer_id)
        else:
            Messagebox.show_info("This feature is for customers only.", "Info", parent=self)

    def update_customer_info(self):
        if hasattr(self.logged_in_user, '_customer_id'):
            self.logged_in_user = db.get_user_by_id(self.logged_in_user._customer_id)
            self.membership_label.config(text=f"Membership: {self.logged_in_user.membership_level}"); self.points_label.config(text=f"Loyalty Points: {self.logged_in_user.loyalty_points}")
    
    def add_to_cart(self, product_obj):
        if product_obj and product_obj.stock > 0:
            self.cart.append(product_obj)
            Messagebox.show_info(f"'{product_obj.name}' has been added to your cart.", "Added", parent=self)
        else:
            Messagebox.show_error("Sorry, this product is currently out of stock.", "Out of Stock", parent=self)
    
    def open_cart(self):
        if not self.cart: Messagebox.show_info("Your shopping cart is empty.", "Empty Cart", parent=self); return
        cart_win = CartPage(self, self.cart, self.logged_in_user); cart_win.grab_set()
    
    def open_membership(self): member_win = MembershipPage(self, self.logged_in_user); member_win.grab_set()
    
    def clear_cart(self): 
        self.cart = []
        # --- THIS IS THE FIX ---
        # We pass the frame 'self.scroll_frame' itself, NOT 'self.scroll_frame.viewport'
        self.load_product_grid(self.scroll_frame) 
        # --- END OF FIX ---
        self.update_customer_info()
    
    def open_admin_panel(self): admin_win = AdminPage(self, self.logged_in_user); admin_win.grab_set()
    
    def load_orders(self):
        for item in self.order_tree.get_children(): self.order_tree.delete(item)
        for sale in db.get_all_sales():
            self.order_tree.insert("", "end", values=(sale['id'], sale['name'], sale['delivery_date'], f"${sale['total_amount']:.2f}"))
            
    def load_customers(self):
        for item in self.customer_tree.get_children(): self.customer_tree.delete(item)
        for user in db.get_all_users():
            if user.role == "Customer":
                self.customer_tree.insert("", tk.END, values=(str(user),))


class CustomerDetailsPage(bs.Toplevel):
    def __init__(self, parent, customer):
        super().__init__(parent)
        self.title(f"👤 Customer Details - {customer.get_name()}")
        self.geometry("450x420")
        self.resizable(False, False)
        self.transient(parent)
        
        main_frame = ttk.Frame(self, padding=25)
        main_frame.pack(expand=True, fill="both")
        
        # Header
        ttk.Label(
            main_frame, 
            text="👤 Customer Details", 
            font=("Segoe UI", 18, "bold"), 
            bootstyle="primary"
        ).pack(pady=(0, 20))
        
        # Details frame
        details_frame = ttk.Labelframe(
            main_frame, 
            text="Information", 
            padding=20,
            bootstyle="info"
        )
        details_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        address = getattr(customer, 'address', 'N/A')
        
        details_text = (
            f"Customer ID: {customer._customer_id}\n\n"
            f"Name: {customer.get_name()}\n\n"
            f"Contact: {customer._contact}\n\n"
            f"Address: {address}\n\n"
            f"Membership Level: {customer.membership_level}\n\n"
            f"Loyalty Points: {customer.loyalty_points}"
        )
                   
        ttk.Label(
            details_frame, 
            text=details_text, 
            justify="left", 
            font=("Segoe UI", 11)
        ).pack(anchor="w")
        
        # Close button
        ttk.Button(
            main_frame, 
            text="Close", 
            command=self.destroy, 
            bootstyle="secondary-outline",
            width=15
        ).pack(side="bottom", pady=(10, 0), ipady=6)

class OrderDetailsPage(bs.Toplevel):
    def __init__(self, parent, sale_id):
        super().__init__(parent)
        self.title(f"📦 Order Details #{sale_id}")
        self.geometry("500x450")
        self.resizable(False, False)
        self.transient(parent)
        
        items = db.get_items_for_sale(sale_id)
        
        main_frame = ttk.Frame(self, padding=25)
        main_frame.pack(expand=True, fill="both")
        
        # Header
        ttk.Label(
            main_frame, 
            text=f"📦 Order Details #{sale_id}", 
            font=("Segoe UI", 18, "bold"), 
            bootstyle="primary"
        ).pack(pady=(0, 20))
        
        # Items frame
        items_frame = ttk.Labelframe(
            main_frame, 
            text="Order Items", 
            padding=20,
            bootstyle="success"
        )
        items_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        if items:
            total = sum(item['price_at_sale'] for item in items)
            for item in items:
                item_text = f"• {item['name']} - ${item['price_at_sale']:.2f}"
                ttk.Label(
                    items_frame, 
                    text=item_text,
                    font=("Segoe UI", 11)
                ).pack(anchor="w", pady=5)
            
            ttk.Separator(items_frame, orient="horizontal").pack(fill="x", pady=10)
            ttk.Label(
                items_frame, 
                text=f"Total: ${total:.2f}",
                font=("Segoe UI", 12, "bold"),
                bootstyle="primary"
            ).pack(anchor="w")
        else:
            ttk.Label(
                items_frame, 
                text="No items found for this order.",
                font=("Segoe UI", 11),
                bootstyle="secondary"
            ).pack(pady=10)
        
        # Close button
        ttk.Button(
            main_frame, 
            text="Close", 
            command=self.destroy, 
            bootstyle="secondary-outline",
            width=15
        ).pack(side="bottom", pady=(10, 0), ipady=6)

class OrderHistoryPage(bs.Toplevel):
    def __init__(self, parent, customer_id):
        super().__init__(parent)
        self.title("📦 My Order History - Fit NZ")
        self.geometry("700x500")
        self.transient(parent)
        
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        ttk.Label(
            main_frame, 
            text="📦 My Order History", 
            font=("Segoe UI", 18, "bold"), 
            bootstyle="primary"
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        # Tree frame
        tree_frame = ttk.Labelframe(
            main_frame, 
            text="Past Orders", 
            padding=15,
            bootstyle="info"
        )
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview
        cols = ("id", "date", "delivery", "total")
        tree = ttk.Treeview(
            tree_frame, 
            columns=cols, 
            show="headings", 
            bootstyle="primary",
            selectmode="browse"
        )
        
        tree.heading("id", text="Order ID", anchor="center")
        tree.column("id", width=100, stretch=False, anchor="center")
        tree.heading("date", text="Date Placed", anchor="center")
        tree.column("date", width=150, anchor="center")
        tree.heading("delivery", text="Est. Delivery", anchor="center")
        tree.column("delivery", width=150, anchor="center")
        tree.heading("total", text="Total Paid", anchor="e")
        tree.column("total", width=150, stretch=False, anchor="e")
        
        tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, 
            orient="vertical", 
            command=tree.yview,
            bootstyle="secondary-round"
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Load orders
        orders = db.get_sales_for_customer(customer_id)
        if orders:
            for sale in orders:
                tree.insert(
                    "", 
                    "end", 
                    values=(
                        sale['id'], 
                        sale['sale_date'], 
                        sale['delivery_date'], 
                        f"${sale['total_amount']:.2f}"
                    )
                )
        else:
            empty_frame = ttk.Frame(tree_frame)
            empty_frame.pack(expand=True)
            ttk.Label(
                empty_frame,
                text="No orders found.",
                font=("Segoe UI", 12),
                bootstyle="secondary"
            ).pack()
        
        # Close button
        ttk.Button(
            main_frame, 
            text="Close", 
            command=self.destroy, 
            bootstyle="secondary-outline",
            width=15
        ).grid(row=2, column=0, pady=(15, 0), sticky="e", ipady=6)