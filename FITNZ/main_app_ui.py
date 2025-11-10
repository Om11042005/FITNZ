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
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        top_bar = ttk.Frame(self, padding=(10, 10, 10, 0)); top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)
        if self.logged_in_user.role in ["Developer", "Manager", "Owner"]:
            ttk.Button(top_bar, text="Admin Panel", bootstyle="info", command=self.open_admin_panel).grid(row=0, column=0, sticky="w")
        
        if self.logged_in_user.role == "Employee":
             user_info = f"Welcome, {self.logged_in_user.name}!"
        else:
            user_info = f"Logged In: {self.logged_in_user.name} ({self.logged_in_user.role})"

        ttk.Label(top_bar, text=user_info, font=("Segoe UI", 10, "italic"), bootstyle="secondary").grid(row=0, column=2, sticky="e")
        ttk.Button(top_bar, text="Logout", command=self.controller.show_login_page, bootstyle="danger-outline").grid(row=0, column=3, sticky="e", padx=10)
        
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL); main_pane.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        left_pane = ttk.Frame(main_pane, padding=5); main_pane.add(left_pane, weight=3)
        right_pane = ttk.Frame(main_pane, padding=5); main_pane.add(right_pane, weight=2)
        left_pane.grid_rowconfigure(0, weight=1); left_pane.grid_columnconfigure(0, weight=1)
        right_pane.grid_rowconfigure(0, weight=1); right_pane.grid_columnconfigure(0, weight=1)

        products_frame = ttk.Labelframe(left_pane, text="Product Inventory & Stock Management", padding=10, bootstyle="info"); products_frame.grid(row=0, column=0, sticky="nsew")
        products_frame.grid_rowconfigure(0, weight=1); products_frame.grid_columnconfigure(0, weight=1)
        cols = ("id", "name", "price", "stock")
        self.product_tree = ttk.Treeview(products_frame, columns=cols, show="tree headings", bootstyle="primary")
        self.product_tree.heading("#0", text="Img", anchor="center")
        self.product_tree.column("#0", width=40, anchor="center", stretch=False)
        self.product_tree.heading("id", text="ID"); self.product_tree.column("id", width=100, stretch=False)
        self.product_tree.heading("name", text="Name"); self.product_tree.column("name", width=200)
        self.product_tree.heading("price", text="Price"); self.product_tree.column("price", width=100, anchor="e")
        self.product_tree.heading("stock", text="Stock"); self.product_tree.column("stock", width=100, anchor="e")
        self.product_tree.grid(row=0, column=0, sticky="nsew")
        ttk.Scrollbar(products_frame, orient="vertical", command=self.product_tree.yview, bootstyle="secondary-round").grid(row=0, column=1, sticky="ns")
        self.product_tree.configure(yscrollcommand=ttk.Scrollbar(products_frame).set)
        
        self.load_products_to_treeview()
        
        action_notebook = ttk.Notebook(products_frame, bootstyle="primary")
        action_notebook.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10,0))
        stock_tab = ttk.Frame(action_notebook, padding=10)
        action_notebook.add(stock_tab, text="Add Stock")
        self.selected_product_label = ttk.Label(stock_tab, text="Selected: None", font=("Segoe UI", 9, "italic"), bootstyle="secondary")
        self.selected_product_label.pack(fill="x")
        ttk.Label(stock_tab, text="Quantity to Add:").pack(fill="x", pady=(10, 5))
        self.stock_entry = ttk.Entry(stock_tab)
        self.stock_entry.pack(side="left", expand=True, fill="x", padx=(0,10))
        ttk.Button(stock_tab, text="Add Stock", command=self.add_stock, bootstyle="success").pack(side="left")

        if self.logged_in_user.role in ["Manager", "Developer", "Owner"]:
            add_tab = ttk.Frame(action_notebook, padding=10)
            action_notebook.add(add_tab, text="Add New Product")
            add_tab.grid_columnconfigure(1, weight=1)
            
            ttk.Label(add_tab, text="Product ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            self.add_id_entry = ttk.Entry(add_tab)
            self.add_id_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            ttk.Label(add_tab, text="Name:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            self.add_name_entry = ttk.Entry(add_tab)
            self.add_name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
            
            ttk.Label(add_tab, text="Price:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
            self.add_price_entry = ttk.Entry(add_tab)
            self.add_price_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            
            ttk.Label(add_tab, text="Stock:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
            self.add_stock_entry = ttk.Entry(add_tab)
            self.add_stock_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
            
            ttk.Label(add_tab, text="Image:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
            self.add_image_label = ttk.Label(add_tab, text="No file selected.", bootstyle="secondary")
            self.add_image_label.grid(row=4, column=1, sticky="ew", padx=5)
            ttk.Button(add_tab, text="Browse...", command=self.browse_for_image, bootstyle="info-outline").grid(row=4, column=2, padx=5, pady=5)
            
            ttk.Button(add_tab, text="Add New Product", command=self.add_product, bootstyle="info").grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=10)

            delete_tab = ttk.Frame(action_notebook, padding=10)
            action_notebook.add(delete_tab, text="Delete Product")
            ttk.Label(delete_tab, text="Select a product from the list above.", bootstyle="secondary").pack(pady=5)
            ttk.Label(delete_tab, text="WARNING: This will remove the product from ALL past sales records.", wraplength=400, bootstyle="danger").pack(pady=5)
            ttk.Button(delete_tab, text="Delete Selected Product", command=self.delete_product, bootstyle="danger").pack(pady=10, fill="x")
        
        self.product_tree.bind("<<TreeviewSelect>>", self.on_product_select_staff)

        right_notebook = ttk.Notebook(right_pane, bootstyle="primary"); right_notebook.grid(row=0, column=0, sticky="nsew")
        if self.logged_in_user.role in ["Developer", "Manager", "Owner"]:
            customers_tab = ttk.Frame(right_notebook); right_notebook.add(customers_tab, text="Customers")
            orders_tab = ttk.Frame(right_notebook); right_notebook.add(orders_tab, text="Recent Orders")
            cust_frame = ttk.Labelframe(customers_tab, text="Customer List", padding=10, bootstyle="info"); cust_frame.pack(expand=True, fill="both", pady=5)
            cust_frame.grid_rowconfigure(0, weight=1); cust_frame.grid_columnconfigure(0, weight=1)
            self.customer_tree = ttk.Treeview(cust_frame, columns=("customer",), show="", bootstyle="primary"); self.customer_tree.column("customer", anchor="w")
            self.customer_tree.grid(row=0, column=0, sticky="nsew")
            cust_actions = ttk.Frame(cust_frame); cust_actions.grid(row=0, column=1, sticky="ns", padx=5)
            ttk.Button(cust_actions, text="View Details", command=self.view_customer_details, bootstyle="info-outline").pack()
            self.load_customers()
            order_frame = ttk.Labelframe(orders_tab, text="All Sales", padding=10, bootstyle="success"); order_frame.pack(expand=True, fill="both", pady=5)
            order_frame.grid_rowconfigure(0, weight=1); order_frame.grid_columnconfigure(0, weight=1)
            order_cols = ("id", "cust", "del_date", "total"); self.order_tree = ttk.Treeview(order_frame, columns=order_cols, show="headings", bootstyle="primary")
            self.order_tree.heading("id", text="ID"); self.order_tree.column("id", width=40, stretch=False)
            self.order_tree.heading("cust", text="Customer"); self.order_tree.heading("del_date", text="Delivery Date")
            self.order_tree.heading("total", text="Total"); self.order_tree.column("total", width=80, stretch=False, anchor="e")
            self.order_tree.grid(row=0, column=0, sticky="nsew")
            order_actions = ttk.Frame(order_frame); order_actions.grid(row=0, column=1, sticky="ns", padx=5)
            ttk.Button(order_actions, text="View Details", command=self.view_order_details, bootstyle="info-outline").pack()
            self.load_orders()
        else:
             welcome_tab = ttk.Frame(right_notebook, padding=20)
             right_notebook.add(welcome_tab, text="Info")
             ttk.Label(welcome_tab, text="Stock Management", font=("Helvetica", 16, "bold"), bootstyle="primary").pack(pady=10)
             ttk.Label(welcome_tab, text="Use the panel on the left to select a product and add new stock.", wraplength=300, justify="center").pack()

    # -----------------------------------------------------------------
    # CUSTOMER UI
    # -----------------------------------------------------------------
    def build_customer_ui(self):
        self.grid_columnconfigure(0, weight=3); self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        
        products_frame = ttk.Labelframe(self, text="Our Products", padding=10, bootstyle="info")
        products_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        products_frame.grid_rowconfigure(0, weight=1); products_frame.grid_columnconfigure(0, weight=1)

        # --- THIS IS THE FIX ---
        # The ScrolledFrame widget is created, and we add widgets to IT, not its viewport
        self.scroll_frame = ScrolledFrame(products_frame, autohide=True)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew")
        
        # Pass the frame 'self.scroll_frame' to the load function
        self.load_product_grid(self.scroll_frame) 
        # --- END OF FIX ---
        
        right_pane = ttk.Frame(self, padding=10)
        right_pane.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        
        self.info_frame = ttk.Labelframe(right_pane, text=f"Welcome, {self.logged_in_user.get_name()}", padding=15, bootstyle="primary")
        self.info_frame.pack(fill="x")
        self.membership_label = ttk.Label(self.info_frame, font=("Helvetica", 11)); self.membership_label.pack(anchor="w")
        self.points_label = ttk.Label(self.info_frame, font=("Helvetica", 11)); self.points_label.pack(anchor="w")
        self.update_customer_info()
        ttk.Button(self.info_frame, text="Manage Membership", command=self.open_membership, bootstyle="info-outline").pack(pady=10, fill="x")
        
        actions_frame = ttk.Labelframe(right_pane, text="Shopping Actions", padding=15, bootstyle="info")
        actions_frame.pack(fill="x", pady=20)
        
        ttk.Button(actions_frame, text="View Cart", command=self.open_cart, bootstyle="primary").pack(fill="x", ipady=5, pady=10)
        ttk.Button(actions_frame, text="My Orders", command=self.open_order_history, bootstyle="info").pack(fill='x', ipady=5)
        
        ttk.Button(right_pane, text="Logout", command=self.controller.show_login_page, bootstyle="danger-outline").pack(side="bottom", fill="x", ipady=5)

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
        self.product_images_list.clear()
        for widget in parent_frame.winfo_children():
            widget.destroy()
            
        products = db.get_all_products()
        MAX_COLS = 3 
        
        for i, p in enumerate(products):
            row = i // MAX_COLS
            col = i % MAX_COLS
            
            card = ttk.Labelframe(parent_frame, text=p.name, padding=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_rowconfigure(0, weight=0)
            card.grid_rowconfigure(1, weight=1)
            card.grid_rowconfigure(2, weight=0)
            card.grid_columnconfigure(0, weight=1)

            photo = self.default_photo_grid
            image_path = get_product_image_path(p.name)
            if image_path:
                try:
                    img = Image.open(image_path)
                    img = img.resize((150, 150), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.product_images_list.append(photo)
                except Exception:
                    photo = self.default_photo_grid
            
            img_label = ttk.Label(card, image=photo, anchor="center")
            img_label.grid(row=0, column=0, pady=5)
            
            info_frame = ttk.Frame(card)
            info_frame.grid(row=1, column=0, pady=5)
            info_frame.grid_columnconfigure((0,1), weight=1)
            
            price_label = ttk.Label(info_frame, text=f"${p.price:.2f}", font=("Helvetica", 12, "bold"))
            price_label.grid(row=0, column=0, sticky="w")
            
            stock_label_text = f"Stock: {p.stock}"
            stock_style = "success" if p.stock > 0 else "danger"
            stock_label = ttk.Label(info_frame, text=stock_label_text, bootstyle=stock_style)
            stock_label.grid(row=0, column=1, sticky="e")
            
            add_btn = ttk.Button(
                card, 
                text="Add to Cart", 
                command=lambda p=p: self.add_to_cart(p),
                bootstyle="success"
            )
            add_btn.grid(row=2, column=0, sticky="ew", pady=(5,0))
            
            if p.stock == 0:
                add_btn.config(state="disabled")
                stock_label.config(text="Out of Stock")

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
        selected_item = self.product_tree.focus()
        if not selected_item: 
            Messagebox.show_warning("Please select a product first.", "No Selection", parent=self)
            return
        try:
            quantity_to_add = int(self.stock_entry.get())
            if quantity_to_add <= 0:
                Messagebox.show_error("Quantity to add must be a positive number.", "Invalid Input", parent=self)
                return
            product_id = self.product_tree.item(selected_item, "values")[0]
            current_product = db.get_product_by_id(product_id)
            if not current_product:
                Messagebox.show_error("Could not find selected product.", "Error", parent=self)
                return
            new_quantity = current_product.stock + quantity_to_add
            if db.update_product_stock(product_id, new_quantity):
                Messagebox.show_info("Stock updated successfully.", "Success", parent=self)
                self.load_products_to_treeview()
                self.stock_entry.delete(0, "end")
                self.selected_product_label.config(text="Selected: None")
            else:
                Messagebox.show_error("Failed to update stock.", "Error", parent=self)
        except ValueError:
            Messagebox.show_error("Please enter a valid number for the quantity.", "Invalid Input", parent=self)

    def add_product(self):
        prod_id = self.add_id_entry.get()
        name = self.add_name_entry.get()
        price_str = self.add_price_entry.get()
        stock_str = self.add_stock_entry.get()
        
        if not all([prod_id, name, price_str, stock_str]):
            Messagebox.show_error("All fields are required.", "Error", parent=self)
            return
        
        if not self.new_product_image_path:
            Messagebox.show_error("Please select an image for the product.", "Error", parent=self)
            return
            
        try:
            price = float(price_str)
            stock = int(stock_str)
        except ValueError:
            Messagebox.show_error("Price and Stock must be valid numbers.", "Error", parent=self)
            return
            
        if price <= 0 or stock < 0:
             Messagebox.show_error("Price must be positive and Stock cannot be negative.", "Error", parent=self)
             return

        try:
            assets_dir = os.path.join('FITNZ', 'assets')
            safe_basename = "".join(c for c in name.lower() if c.isalnum() or c == ' ').replace(' ', '_')
            file_extension = os.path.splitext(self.new_product_image_path)[1]
            destination_filename = safe_basename + file_extension
            destination_path = os.path.join(assets_dir, destination_filename)
            
            shutil.copy(self.new_product_image_path, destination_path)
            
        except Exception as e:
            Messagebox.show_error(f"Failed to save image: {e}", "Error", parent=self)
            return
            
        if db.add_product(prod_id, name, price, stock):
            Messagebox.show_info("Product added successfully.", "Success", parent=self)
            self.load_products_to_treeview()
            
            self.add_id_entry.delete(0, "end")
            self.add_name_entry.delete(0, "end")
            self.add_price_entry.delete(0, "end")
            self.add_stock_entry.delete(0, "end")
            self.new_product_image_path = None
            self.add_image_label.config(text="No file selected.")
        else:
            Messagebox.show_error("Failed to add product. The Product ID might already exist.", "Error", parent=self)
            if os.path.exists(destination_path):
                os.remove(destination_path)

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
        super().__init__(parent); self.title(f"Details for {customer.get_name()}"); self.geometry("4F00x300")
        frame = ttk.Frame(self, padding=20); frame.pack(expand=True, fill="both")
        
        address = getattr(customer, 'address', 'N/A')
        
        details = (f"Customer ID: {customer._customer_id}\n"
                   f"Name: {customer.get_name()}\n"
                   f"Contact: {customer._contact}\n"
                   f"Address: {address}\n\n"
                   f"Membership: {customer.membership_level}\n"
                   f"Loyalty Points: {customer.loyalty_points}")
                   
        ttk.Label(frame, text=details, justify="left", font=("Segoe UI", 11)).pack(anchor="w")
        ttk.Button(frame, text="Close", command=self.destroy, bootstyle="secondary").pack(side="bottom", pady=10)

class OrderDetailsPage(bs.Toplevel):
    def __init__(self, parent, sale_id):
        super().__init__(parent); self.title(f"Order Details #{sale_id}"); self.minsize(400, 300)
        items = db.get_items_for_sale(sale_id)
        frame = ttk.Frame(self, padding=20); frame.pack(expand=True, fill="both")
        ttk.Label(frame, text=f"Items in Order #{sale_id}", font=("Helvetica", 14, "bold"), bootstyle="info").pack(pady=(0,10))
        for item in items:
            ttk.Label(frame, text=f"- {item['name']} (${item['price_at_sale']:.2f})").pack(anchor="w")
        ttk.Button(frame, text="Close", command=self.destroy, bootstyle="secondary").pack(side="bottom", pady=10)

class OrderHistoryPage(bs.Toplevel):
    def __init__(self, parent, customer_id):
        super().__init__(parent); self.title("My Order History"); self.minsize(500, 400)
        frame = ttk.Frame(self, padding=10); frame.pack(expand=True, fill="both")
        frame.grid_rowconfigure(0, weight=1); frame.grid_columnconfigure(0, weight=1)
        cols = ("id", "date", "delivery", "total"); tree = ttk.Treeview(frame, columns=cols, show="headings", bootstyle="primary")
        tree.heading("id", text="Order ID"); tree.column("id", width=60)
        tree.heading("date", text="Date Placed"); tree.heading("delivery", text="Est. Delivery")
        tree.heading("total", text="Total Paid"); tree.column("total", anchor="e")
        tree.grid(row=0, column=0, sticky="nsew")
        for sale in db.get_sales_for_customer(customer_id):
            tree.insert("", "end", values=(sale['id'], sale['sale_date'], sale['delivery_date'], f"${sale['total_amount']:.2f}"))
        ttk.Button(frame, text="Close", command=self.destroy, bootstyle="secondary").grid(row=1, column=0, pady=10)