# File: FITNZ/main_app_ui.py
import tkinter as tk
from tkinter import filedialog
from datetime import date, datetime, timedelta
import ttkbootstrap as bs
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from PIL import Image, ImageTk
import os
from . import database_mysql as db
from .admin_ui import AdminPage
from .customer_ui import CartPage, MembershipPage

class MainAppPage(ttk.Frame):
    """Main application interface after login"""
    
    def __init__(self, parent, controller, logged_in_user):
        super().__init__(parent)
        self.controller = controller
        self.logged_in_user = logged_in_user
        self.cart = []
        self.current_customer = None
        self.sale_items = []  # For staff: list of dicts with product and quantity
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self, padding=10, bootstyle="dark")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # App title
        title_label = ttk.Label(
            header_frame,
            text="🏋️ Fit NZ - Retail POS System",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-dark"
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # User info
        user_info = ttk.Label(
            header_frame,
            text=f"Welcome, {self.logged_in_user.name} ({self.logged_in_user.role})",
            font=("Segoe UI", 10),
            bootstyle="inverse-dark"
        )
        user_info.grid(row=0, column=1, sticky="e")
        
        # Main content area
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Show appropriate interface based on user role
        if self.logged_in_user.role == "Customer":
            self.create_customer_interface()
        else:
            self.create_staff_interface()
            
        # Footer with logout button
        footer_frame = ttk.Frame(self, padding=10)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        logout_btn = ttk.Button(
            footer_frame,
            text="🚪 Logout",
            command=self.logout,
            bootstyle="danger-outline",
            width=15
        )
        logout_btn.grid(row=0, column=1, sticky="e")
      
# ===============================================
# Code Owner: Rajina (US: Product Browsing/Details)
# # ===============================================


    def create_customer_interface(self):
        """Create customer-specific interface"""
        # Products frame
        products_frame = ttk.Labelframe(
            self.main_frame,
            text="🛍️ Available Products",
            padding=15,
            bootstyle="info"
        )
        products_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        products_frame.grid_rowconfigure(1, weight=1)
        products_frame.grid_columnconfigure(0, weight=1)
        
        # Products treeview
        tree_frame = ttk.Frame(products_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        columns = ("ID", "Name", "Price", "Stock")
        self.products_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            bootstyle="primary",
            selectmode="browse"
        )
        
        # Configure columns
        self.products_tree.heading("ID", text="Product ID")
        self.products_tree.column("ID", width=80, anchor="center")
        self.products_tree.heading("Name", text="Product Name")
        self.products_tree.column("Name", width=200, anchor="w")
        self.products_tree.heading("Price", text="Price ($)")
        self.products_tree.column("Price", width=100, anchor="e")
        self.products_tree.heading("Stock", text="Stock")
        self.products_tree.column("Stock", width=80, anchor="center")
        
        self.products_tree.grid(row=0, column=0, sticky="nsew")
        
        # Add double-click event to view product details
        self.products_tree.bind('<Double-1>', lambda e: self.view_product_details())
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.products_tree.yview,
            bootstyle="secondary-round"
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        
        # Load products
        self.load_products()
        
        # Customer actions frame
        actions_frame = ttk.Frame(products_frame)
        actions_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        
        ttk.Button(
            actions_frame,
            text="🛒 Add to Cart",
            command=self.add_to_cart,
            bootstyle="success-outline",
            width=15
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="👁️ View Details",
            command=self.view_product_details,
            bootstyle="primary-outline",
            width=15
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="⭐ Membership",
            command=self.manage_membership,
            bootstyle="warning-outline",
            width=15
        ).pack(side="left")
        
        ttk.Button(
            actions_frame,
            text="📦 Order History",
            command=self.open_order_history,
            bootstyle="info-outline",
            width=15
        ).pack(side="left")

        # Customer info frame
        info_frame = ttk.Labelframe(
            self.main_frame,
            text="👤 Customer Information",
            padding=15,
            bootstyle="success"
        )
        info_frame.grid(row=0, column=1, sticky="nsew", padx=(15, 0), pady=(0, 15))
        
        # Display customer details
        ttk.Label(
            info_frame,
            text=f"Name: {self.logged_in_user.get_name()}",
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=5)
        
        ttk.Label(
            info_frame,
            text=f"Membership: {getattr(self.logged_in_user, 'membership_level', 'Standard')}",
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=5)
        
        ttk.Label(
            info_frame,
            text=f"Loyalty Points: {getattr(self.logged_in_user, 'loyalty_points', 0)}",
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=5)
        
        # Configure column weights
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)

    def open_order_history(self):
        if not self.logged_in_user:
            Messagebox.show_error("No customer logged in.", "Error", parent=self)
            return

        win = CustomerOrderHistoryPage(self, self.logged_in_user)
        win.grab_set()






#Umang Part





# Imran Part



    def add_to_cart(self):
        """Add selected product to cart"""
        selected = self.products_tree.selection()
        if not selected:
            Messagebox.show_warning("Please select a product to add to cart.", "No Selection", parent=self)
            return
            
        product_id = self.products_tree.item(selected[0])['values'][0]
        product = db.get_product_by_id(product_id)
        
        if product:
            self.cart.append(product)
            Messagebox.show_info(f"Added {product.name} to cart!", "Success", parent=self)
        else:
            Messagebox.show_error("Failed to add product to cart.", "Error", parent=self)
    
    def view_cart(self):
        """Open cart window"""
        if not self.cart:
            Messagebox.show_info("Your cart is empty.", "Empty Cart", parent=self)
            return
            
        cart_window = CartPage(self, self.cart, self.logged_in_user)
        cart_window.grab_set()
    
    def manage_membership(self):
        """Open membership management window"""
        membership_window = MembershipPage(self, self.logged_in_user)
        membership_window.grab_set()
    
    def view_product_details(self):
        """View detailed product information"""
        selected = self.products_tree.selection()
        if not selected:
            Messagebox.show_warning("Please select a product to view details.", "No Selection", parent=self)
            return
        
        product_id = self.products_tree.item(selected[0])['values'][0]
        product = db.get_product_by_id(product_id)
        
        if product:
            # Determine user role for appropriate actions
            user_role = self.logged_in_user.role if hasattr(self.logged_in_user, 'role') else "Customer"
            ProductDetailsPage(self, product, user_role)
        else:
            Messagebox.show_error("Product not found.", "Error", parent=self)
    
    def quick_view_product(self, product_id):
        """Quick view product details (for double-click)"""
        product = db.get_product_by_id(product_id)
        if product:
            user_role = self.logged_in_user.role if hasattr(self.logged_in_user, 'role') else "Customer"
            ProductDetailsPage(self, product, user_role)
    
    def complete_sale(self):
        """Called after successful payment to clear the sale"""
        self.sale_items.clear()
        self.update_sale_display()
        self.load_products()  # Refresh product stock
    
    def clear_cart(self):
        """Clear the shopping cart"""
        self.cart.clear()
    
    def update_customer_info(self):
        """Refresh customer information after membership changes"""
        # This would typically reload customer data from database
        pass
    
    def logout(self):
        """Log out and return to login page"""
        result = Messagebox.yesno("Are you sure you want to logout?", "Confirm Logout", parent=self)
        if result == "Yes":
            self.controller.show_login_page()


class ProductDetailsPage(bs.Toplevel):
    """Full-screen product details window with images and descriptions"""
    
    def __init__(self, parent, product, user_role="Customer"):
        super().__init__(parent)
        self.parent = parent
        self.product = product
        self.user_role = user_role
        
        # Make window full screen
        self.title(f"📦 {product.name} - Product Details")
        self.state('zoomed')  # Full screen
        self.transient(parent)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the product details interface"""
        # Main container
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header with back button
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Back button - MAKE VISIBLE
        back_btn = ttk.Button(
            header_frame,
            text="← Back",
            command=self.destroy,
            bootstyle="secondary-outline",
            width=15
        )
        back_btn.grid(row=0, column=0, sticky="w")
        
        # Product title
        ttk.Label(
            header_frame,
            text=f"📦 {self.product.name}",
            font=("Segoe UI", 24, "bold"),
            bootstyle="primary"
        ).grid(row=0, column=1, sticky="ew")
        
        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Left column - Product image and basic info
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Product image section
        image_frame = ttk.Labelframe(
            left_frame,
            text="Product Image",
            padding=20,
            bootstyle="info"
        )
        image_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        
        # Product image - FIX IMAGE DISPLAY FOR EMPLOYEES
        # Try to load actual image first, fall back to emoji
        product_image = self.load_product_image(self.product)
        if product_image:
            self.image_label = ttk.Label(
                image_frame,
                image=product_image,
                bootstyle="light",
                anchor="center"
            )
            self.image_label.image = product_image  # Keep reference
            self.image_label.pack(expand=True, fill="both")
        else:
            product_emoji = self.get_product_emoji(self.product)
            self.image_label = ttk.Label(
                image_frame,
                text=product_emoji,
                font=("Segoe UI", 72),
                bootstyle="light",
                anchor="center"
            )
            self.image_label.pack(expand=True, fill="both")
        
        # Stock and price info
        info_frame = ttk.Labelframe(
            left_frame,
            text="Product Information",
            padding=20,
            bootstyle="success"
        )
        info_frame.grid(row=1, column=0, sticky="nsew")
        
        # Product details
        details = [
            ("🆔 Product ID", self.product.product_id),
            ("💰 Price", f"${self.product.price:.2f}"),
            ("📦 Stock Available", f"{self.product.stock} units"),
            ("🏷️ Category", self.determine_category(self.product.name)),
            ("⭐ Status", self.get_stock_status(self.product.stock))
        ]
        
        for i, (label, value) in enumerate(details):
            detail_frame = ttk.Frame(info_frame)
            detail_frame.pack(fill="x", pady=5)
            
            ttk.Label(
                detail_frame,
                text=label,
                font=("Segoe UI", 11, "bold"),
                width=20
            ).pack(side="left")
            
            ttk.Label(
                detail_frame,
                text=str(value),
                font=("Segoe UI", 11),
                bootstyle="primary"
            ).pack(side="left")
        
        # Right column - Product description and actions
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Product description
        desc_frame = ttk.Labelframe(
            right_frame,
            text="📝 Product Description",
            padding=20,
            bootstyle="primary"
        )
        desc_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        desc_frame.grid_rowconfigure(0, weight=1)
        desc_frame.grid_columnconfigure(0, weight=1)
        
        # Description text with scrollbar
        desc_text_frame = ttk.Frame(desc_frame)
        desc_text_frame.grid(row=0, column=0, sticky="nsew")
        desc_text_frame.grid_rowconfigure(0, weight=1)
        desc_text_frame.grid_columnconfigure(0, weight=1)
        
        self.desc_text = tk.Text(
            desc_text_frame,
            wrap="word",
            font=("Segoe UI", 11),
            bg="#f8f9fa",
            relief="flat",
            padx=10,
            pady=10,
            height=10
        )
        self.desc_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for description
        desc_scrollbar = ttk.Scrollbar(
            desc_text_frame,
            orient="vertical",
            command=self.desc_text.yview,
            bootstyle="secondary-round"
        )
        desc_scrollbar.grid(row=0, column=1, sticky="ns")
        self.desc_text.configure(yscrollcommand=desc_scrollbar.set)
        
        # Load product description
        self.load_product_description()
        
        # Product specifications
        specs_frame = ttk.Labelframe(
            right_frame,
            text="⚙️ Product Specifications",
            padding=20,
            bootstyle="warning"
        )
        specs_frame.grid(row=1, column=0, sticky="nsew")
        specs_frame.grid_rowconfigure(0, weight=1)
        specs_frame.grid_columnconfigure(0, weight=1)
        
        # Specifications text
        specs_text_frame = ttk.Frame(specs_frame)
        specs_text_frame.grid(row=0, column=0, sticky="nsew")
        specs_text_frame.grid_rowconfigure(0, weight=1)
        specs_text_frame.grid_columnconfigure(0, weight=1)
        
        self.specs_text = tk.Text(
            specs_text_frame,
            wrap="word",
            font=("Segoe UI", 10),
            bg="#fffbf0",
            relief="flat",
            padx=10,
            pady=10,
            height=8
        )
        self.specs_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for specifications
        specs_scrollbar = ttk.Scrollbar(
            specs_text_frame,
            orient="vertical",
            command=self.specs_text.yview,
            bootstyle="secondary-round"
        )
        specs_scrollbar.grid(row=0, column=1, sticky="ns")
        self.specs_text.configure(yscrollcommand=specs_scrollbar.set)
        
        # Load product specifications
        self.load_product_specifications()
        
        # Action buttons frame (at the bottom) - MAKE BUTTONS VISIBLE
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        
        if self.user_role == "Customer":
            # Customer actions - MAKE BUTTONS LARGER AND MORE VISIBLE
            ttk.Button(
                action_frame,
                text="🛒 Add to Cart",
                command=self.add_to_cart,
                bootstyle="success",
                width=20
            ).grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=12)  # Increased ipady for better visibility
            
            ttk.Button(
                action_frame,
                text="⭐ Add to Wishlist",
                command=self.add_to_wishlist,
                bootstyle="warning-outline",
                width=20
            ).grid(row=0, column=1, sticky="ew", padx=(10, 0), ipady=12)
        else:
            # Staff actions - MAKE BUTTONS LARGER AND MORE VISIBLE
            ttk.Button(
                action_frame,
                text="➕ Add to Current Sale",
                command=self.add_to_sale,
                bootstyle="success",
                width=20
            ).grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=12)
            
            ttk.Button(
                action_frame,
                text="📊 View Sales History",
                command=self.view_sales_history,
                bootstyle="info-outline",
                width=20
            ).grid(row=0, column=1, sticky="ew", padx=(10, 0), ipady=12)
    
    def load_product_image(self, product):
        """Try to load actual product image, return None if not available"""
        # Check for image in assets folder
        assets_dir = "assets"
        if os.path.exists(assets_dir):
            # Look for image files that might match the product
            possible_files = [
                f"{product.product_id}.png",
                f"{product.product_id}.jpg",
                f"{product.product_id}.jpeg",
                f"{product.name.replace(' ', '_').lower()}.png",
                f"{product.name.replace(' ', '_').lower()}.jpg",
            ]
            
            for filename in possible_files:
                filepath = os.path.join(assets_dir, filename)
                if os.path.exists(filepath):
                    try:
                        image = Image.open(filepath)
                        image.thumbnail((300, 300))  # Resize to fit
                        return ImageTk.PhotoImage(image)
                    except Exception as e:
                        print(f"Error loading image {filepath}: {e}")
                        continue
        return None
    
    def get_product_emoji(self, product):
        """Get product emoji placeholder"""
        category = self.determine_category(product.name).lower()
        
        image_emojis = {
            'nutrition': '🥛',
            'weights': '🏋️',
            'yoga': '🧘',
            'cardio': '🏃',
            'accessories': '🎽',
            'equipment': '⚙️'
        }
        
        return image_emojis.get(category, '📦')
    
    def determine_category(self, product_name):
        """Determine product category based on name"""
        name_lower = product_name.lower()
        if any(word in name_lower for word in ['protein', 'supplement', 'vitamin', 'creatine', 'whey']):
            return "Nutrition"
        elif any(word in name_lower for word in ['dumbbell', 'barbell', 'kettlebell', 'weight']):
            return "Weights"
        elif any(word in name_lower for word in ['yoga', 'mat', 'pilates']):
            return "Yoga"
        elif any(word in name_lower for word in ['band', 'rope', 'strap', 'gloves']):
            return "Accessories"
        elif any(word in name_lower for word in ['treadmill', 'bike', 'elliptical']):
            return "Cardio"
        else:
            return "Equipment"
    
    def get_stock_status(self, stock):
        """Get stock status message"""
        if stock > 20:
            return "✅ In Stock"
        elif stock > 10:
            return "🟡 Limited Stock"
        elif stock > 0:
            return "🟠 Low Stock"
        else:
            return "🔴 Out of Stock"
    
    def load_product_description(self):
        """Load product description based on product type"""
        category = self.determine_category(self.product.name)
        descriptions = {
            "Nutrition": f"""
{self.product.name} is a premium fitness supplement designed to support your workout goals.

🔸 High-quality ingredients for optimal results
🔸 Perfect for pre-workout or post-workout recovery
🔸 Easy to mix and great tasting
🔸 Supports muscle growth and recovery

Ideal for athletes, bodybuilders, and fitness enthusiasts looking to enhance their performance and achieve their fitness goals faster.

💡 Usage Recommendation: 
- Mix one serving with water or milk
- Consume 30 minutes before workout or immediately after
- Can be used as a meal replacement

Storage: Keep in a cool, dry place away from direct sunlight.
""",
            "Weights": f"""
{self.product.name} - Professional grade fitness equipment for serious training.

🔸 Durable construction for long-lasting use
🔸 Ergonomic design for comfortable grip
🔸 Perfect for strength training and muscle building
🔸 Suitable for home gyms and commercial facilities

Built to withstand intense workouts while providing the reliability you need for consistent training progress.

🏋️ Features:
- High-quality materials
- Secure grip handles
- Balanced weight distribution
- Rust-resistant coating

Safety Tips:
- Always use proper form
- Start with lighter weights
- Use spotter for heavy lifts
- Store in dry area
""",
            "Yoga": f"""
{self.product.name} - Enhance your yoga practice with this premium equipment.

🔸 Eco-friendly materials
🔸 Non-slip surface for safety
🔸 Perfect for all yoga styles
🔸 Portable and easy to clean

Designed to support your yoga journey with comfort and stability, whether you're a beginner or advanced practitioner.

🧘 Benefits:
- Improves practice stability
- Provides cushioning and support
- Enhances alignment and posture
- Durable and long-lasting

Care Instructions:
- Wipe clean with damp cloth
- Air dry completely
- Store rolled or flat
- Avoid direct sunlight
""",
            "Cardio": f"""
{self.product.name} - Professional cardio equipment for effective workouts.

🔸 Advanced fitness tracking
🔸 Smooth and quiet operation
🔸 Adjustable intensity levels
🔸 Space-efficient design

Engineered for optimal cardiovascular workouts with features that make every session effective and enjoyable.

🏃 Technical Specifications:
- Multiple workout programs
- Heart rate monitoring
- Distance and calorie tracking
- User profiles support

Maintenance:
- Regular lubrication
- Clean after each use
- Check bolts periodically
- Professional servicing recommended
""",
            "Accessories": f"""
{self.product.name} - Essential fitness accessories for complete workouts.

🔸 Versatile and multi-functional
🔸 Portable and lightweight
🔸 Durable construction
🔸 Suitable for various exercises

The perfect addition to any workout routine, providing support and enhancement for your fitness activities.

🎽 Usage:
- Resistance training
- Mobility exercises
- Rehabilitation workouts
- Sports training

Features:
- Adjustable resistance
- Comfortable grip
- Easy to store
- Travel-friendly
""",
            "Equipment": f"""
{self.product.name} - Professional fitness equipment for comprehensive training.

🔸 Commercial grade quality
🔸 Adjustable settings
🔸 Safety features included
🔸 Easy to assemble

Built to professional standards with attention to detail and user safety for effective and safe workouts.

⚙️ Specifications:
- Heavy-duty construction
- Multiple adjustment points
- Weight capacity: 300lbs+
- Assembly required

Safety Features:
- Secure locking mechanisms
- Emergency stop
- Non-slip surfaces
- Stability enhancements
"""
        }
        
        description = descriptions.get(category, f"""
{self.product.name} - A high-quality fitness product from Fit NZ.

This product is designed to help you achieve your fitness goals with reliability and performance. Whether you're setting up a home gym or enhancing your commercial facility, this product delivers the quality you expect from Fit NZ.

🔸 Premium quality materials
🔸 Designed for durability and performance
🔸 Suitable for various fitness levels
🔸 Backed by our satisfaction guarantee

At Fit NZ, we're committed to providing products that help you on your fitness journey. This item is part of our carefully selected range of fitness equipment and accessories.

For any questions about this product or assistance with your purchase, please contact our customer service team.
""")
        
        self.desc_text.insert("1.0", description)
        self.desc_text.config(state="disabled")
    
    def load_product_specifications(self):
        """Load product specifications"""
        category = self.determine_category(self.product.name)
        
        specs_templates = {
            "Nutrition": f"""
Product: {self.product.name}
Category: Sports Nutrition
Serving Size: 1 scoop (30g)
Servings per Container: 30
Price per Serving: ${self.product.price/30:.2f}

📊 Nutritional Information (per serving):
• Calories: 120 kcal
• Protein: 24g
• Carbohydrates: 3g
• Fat: 1g
• Sugar: 1g

🎯 Key Features:
• High Protein Content
• Low Sugar
• Fast Absorption
• Great Taste

🏷️ Additional Info:
• Flavor: Chocolate
• Brand: Fit NZ Premium
• Suitable for: Vegetarians
• Certification: GMP Certified
""",
            "Weights": f"""
Product: {self.product.name}
Category: Strength Training
Material: Cast Iron with Rubber Coating
Color: Black

📐 Physical Specifications:
• Weight: {self.product.price/10:.1f} lbs each
• Diameter: 6-8 inches
• Handle: Knurled for grip
• Coating: Rubberized

⚙️ Features:
• Durable Construction
• Non-slip Surface
• Floor Protection
• Long-lasting

🏷️ Additional Info:
• Pair: Sold individually
• Warranty: 2 years
• Usage: Home & Commercial
• Storage: Dry area recommended
""",
            "Yoga": f"""
Product: {self.product.name}
Category: Yoga & Pilates
Material: TPE Eco-friendly
Thickness: 6mm

📐 Physical Specifications:
• Dimensions: 72" x 24"
• Weight: 2.5 lbs
• Texture: Non-slip surface
• Color: Various available

🧘 Features:
• Eco-friendly Materials
• Excellent Grip
• Easy to Clean
• Portable Design

🏷️ Additional Info:
• Included: Carry strap
• Care: Wipe clean
• Usage: All yoga types
• Certification: Eco-certified
""",
            "Cardio": f"""
Product: {self.product.name}
Category: Cardio Equipment
Power: Electric/Manual
Display: LCD Monitor

📐 Technical Specifications:
• Dimensions: 60" x 28" x 50"
• Weight Capacity: 300 lbs
• Programs: 12 preset
• Resistance: Magnetic

🏃 Features:
• Heart Rate Monitoring
• Calorie Tracking
• Distance Measurement
• Pulse Sensors

🏷️ Additional Info:
• Assembly: Required
• Warranty: 5 years frame
• Delivery: White glove available
• Support: 24/7 customer service
""",
            "Accessories": f"""
Product: {self.product.name}
Category: Fitness Accessories
Material: Latex/Nylon
Length: Varies

📐 Specifications:
• Resistance Levels: 5
• Maximum Stretch: 200%
• Handles: Comfort grip
• Color: Assorted

💪 Features:
• Portable Design
• Multiple Resistance Levels
• Durable Materials
• Versatile Use

🏷️ Additional Info:
• Set Includes: 5 bands
• Storage: Carry bag included
• Usage: Full body workouts
• Level: Beginner to Advanced
""",
            "Equipment": f"""
Product: {self.product.name}
Category: Gym Equipment
Frame: Steel Construction
Finish: Powder Coated

📐 Specifications:
• Weight Capacity: 500 lbs
• Dimensions: Varies by setup
• Adjustment: Multiple points
• Assembly: Tools included

⚙️ Features:
• Commercial Grade
• Adjustable Settings
• Safety Locking
• Stable Base

🏷️ Additional Info:
• Warranty: Lifetime frame
• Delivery: Professional installation available
• Support: Detailed manual included
• Maintenance: Regular inspection recommended
"""
        }
        
        specs = specs_templates.get(category, f"""
Product: {self.product.name}
Category: {category}
Price: ${self.product.price:.2f}
Stock: {self.product.stock} units

📊 Basic Information:
• Product ID: {self.product.product_id}
• Category: {category}
• Current Stock: {self.product.stock}
• Price: ${self.product.price:.2f}

🎯 Product Features:
• High Quality Materials
• Durable Construction
• User Friendly Design
• Reliable Performance

🏷️ Additional Details:
• Brand: Fit NZ
• Satisfaction Guarantee
• Customer Support Available
• Quality Assured
""")
        
        self.specs_text.insert("1.0", specs)
        self.specs_text.config(state="disabled")
    
    def add_to_cart(self):
        """Add product to cart (customer)"""
        if hasattr(self.parent, 'cart'):
            self.parent.cart.append(self.product)
            Messagebox.show_info(
                f"Added {self.product.name} to your cart!",
                "Success",
                parent=self
            )
        else:
            Messagebox.show_info(
                "Product added to cart!",
                "Success", 
                parent=self
            )
    
    def add_to_wishlist(self):
        """Add product to wishlist"""
        Messagebox.show_info(
            f"Added {self.product.name} to your wishlist!",
            "Wishlist Updated",
            parent=self
        )
    
    def add_to_sale(self):
        """Add product to current sale (staff)"""
        if hasattr(self.parent, 'sale_items'):
            # Check if product already in sale
            for item in self.parent.sale_items:
                if item['product'].product_id == self.product.product_id:
                    item['quantity'] += 1
                    Messagebox.show_info(
                        f"Added another {self.product.name} to current sale!",
                        "Sale Updated",
                        parent=self
                    )
                    return
            
            # Add new product to sale
            self.parent.sale_items.append({
                'product': self.product,
                'quantity': 1
            })
            
            if hasattr(self.parent, 'update_sale_display'):
                self.parent.update_sale_display()
            
            Messagebox.show_info(
                f"Added {self.product.name} to current sale!",
                "Sale Updated",
                parent=self
            )
        else:
            Messagebox.show_info(
                "Product added to sale!",
                "Success",
                parent=self
            )
    
    def view_sales_history(self):
        """View sales history for this product"""
        Messagebox.show_info(
            f"Sales history for {self.product.name}\n\n"
            f"Total Sold: Calculating...\n"
            f"Revenue: Calculating...\n"
            f"Popularity: High\n",
            "Sales History",
            parent=self
        )


class ProductManagementPage(bs.Toplevel):
    """Full product management UI (Manager/Owner/Developer only)."""

    def __init__(self, parent, logged_in_user):
        super().__init__(parent)
        self.logged_in_user = logged_in_user

        self.title("📦 Product Management - Fit NZ")
        self.minsize(850, 600)
        self.transient(parent)

        # ===== HEADER (PACK) =====
        header = ttk.Frame(self, padding=20)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="📦 Product Management",
            font=("Segoe UI", 20, "bold"),
            bootstyle="primary"
        ).pack(side="left")

        ttk.Label(
            header,
            text=f"Logged in as: {logged_in_user.name}",
            font=("Segoe UI", 10),
            bootstyle="secondary"
        ).pack(side="right")

        # ===== CONTENT AREA (PACK) =====
        content = ttk.Frame(self, padding=20)
        content.pack(fill="both", expand=True)

        # ===== LEFT: PRODUCT LIST =====
        list_frame = ttk.Labelframe(
            content,
            text="Product Inventory",
            padding=15,
            bootstyle="info"
        )
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Tree container (GRID only inside)
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True)

        columns = ("ID", "Name", "Price", "Stock")
        self.product_tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            bootstyle="primary",
            height=20,
        )

        self.product_tree.heading("ID", text="Product ID")
        self.product_tree.heading("Name", text="Product Name")
        self.product_tree.heading("Price", text="Price ($)")
        self.product_tree.heading("Stock", text="Stock")

        self.product_tree.column("ID", width=120, anchor="center")
        self.product_tree.column("Name", width=220, anchor="w")
        self.product_tree.column("Price", width=100, anchor="e")
        self.product_tree.column("Stock", width=100, anchor="center")

        self.product_tree.grid(row=0, column=0, sticky="nsew")

        tree_scroll = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self.product_tree.yview
        )
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.product_tree.configure(yscrollcommand=tree_scroll.set)

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # ===== RIGHT: BUTTONS =====
        right_actions = ttk.Frame(content)
        right_actions.pack(side="right", fill="y")

        ttk.Button(
            right_actions,
            text="➕ Add Product",
            bootstyle="success",
            width=18,
            command=self.open_add_product
        ).pack(pady=10)

        ttk.Button(
            right_actions,
            text="✏️ Edit Product",
            bootstyle="primary",
            width=18,
            command=self.open_edit_product
        ).pack(pady=10)

        ttk.Button(
            right_actions,
            text="🗑️ Delete Product",
            bootstyle="danger",
            width=18,
            command=self.delete_product
        ).pack(pady=10)

        ttk.Button(
            right_actions,
            text="🔄 Refresh",
            bootstyle="info-outline",
            width=18,
            command=self.load_products
        ).pack(pady=10)

        ttk.Button(
            right_actions,
            text="← Back",
            bootstyle="secondary-outline",
            width=18,
            command=self.destroy
        ).pack(pady=40)

        # Load current products
        self.load_products()

# Umang part

    
# ===============================================
# Code Owner: Sahil (US: Checkout/Order History/Stock Alerts)
# ===============================================
    def process_payment(self, payment_method):
        """Process the sale with the given payment method"""
        try:
            # Prepare products for database
            products_for_db = []
            for item in self.sale_items:
                # Add each product quantity times
                for _ in range(item['quantity']):
                    products_for_db.append(item['product'])
            
            # Calculate delivery date (next day for in-store)
            delivery_date = date.today()
            
            # Process sale
            success = db.process_sale(
                self.customer,
                products_for_db,
                self.points_redeemed,
                False,  # student_discount_applied
                delivery_date,
            )
            
            if success:
                # --- LOYALTY POINT UPDATE ---
                if self.customer:
                    old = getattr(self.customer, "loyalty_points", 0)
                    used = self.points_redeemed
                    spent = self.total

                    # Deduct used points
                    remaining = max(0, old - used)

                    # Earn new points (1 point per $10 spent)
                    earned = int(spent // 10)

                    final_points = remaining + earned

                    # Get correct customer ID safely
                    cust_id = (
                        getattr(self.customer, "customer_id", None)
                        or getattr(self.customer, "_customer_id", None)
                        or getattr(self.customer, "id", None)
                    )

                    # Save to database
                    if cust_id:
                        db.update_customer_points(cust_id, final_points)

                    # Update in memory
                    self.customer.loyalty_points = final_points

                # Continue to receipt
                self.show_receipt(payment_method)
            else:
                Messagebox.show_error("Failed to process sale. Please try again.", "Error", parent=self)
                
        except Exception as e:
            Messagebox.show_error(f"An error occurred: {str(e)}", "Error", parent=self)

    def show_receipt(self, payment_method):
        """
        Modified to include GST, points redeemed, and remaining points.
        """

        success, remaining_points, gst_total, grand_total = db.process_sale(
            self.customer,
            [item['product'] for item in self.sale_items for _ in range(item['quantity'])],
            self.points_redeemed,
            False,  # student discount not used here
            date.today()
        )

        if not success:
            Messagebox.show_error("Failed to process sale.", "Error", parent=self)
            return

        # Build receipt info with new fields
        receipt_items = []
        for item in self.sale_items:
            receipt_items.append({
                'name': item['product'].name,
                'price': item['product'].price,
                'quantity': item['quantity'],
                'total': item['product'].price * item['quantity']
            })

        receipt_info = {
            'items': receipt_items,
            'subtotal': self.subtotal,
            'discount': self.discount_applied,
            'points_redeemed': self.points_redeemed,
            'remaining_points': remaining_points,
            'gst': gst_total,
            'total': grand_total,
            'payment_method': payment_method,
            'customer': self.customer.get_name() if self.customer else "Walk-in Customer",
            'employee': self.employee.name,
            'date': date.today().strftime("%Y-%m-%d"),
            'time': datetime.now().strftime("%H:%M:%S")
        }

        receipt_text = self.generate_receipt_text(receipt_info)

        Messagebox.show_info(
            receipt_text,
            "🎉 Sale Completed!",
            parent=self
        )

        # Clear cart
        if hasattr(self.parent, 'complete_sale'):
            self.parent.complete_sale()

        self.destroy()


    def generate_receipt_text(self, r):
        """Generate updated receipt with GST + loyalty points."""
        
        receipt = "═══════════════════════════════\n"
        receipt += "           FIT NZ STORE\n"
        receipt += "      Fitness Equipment & Nutrition\n"
        receipt += "═══════════════════════════════\n\n"

        receipt += f"Date: {r['date']} {r['time']}\n"
        receipt += f"Customer: {r['customer']}\n"
        receipt += f"Staff: {r['employee']}\n"
        receipt += "───────────────────────────────\n"
        receipt += "ITEMS:\n"

        for item in r['items']:
            receipt += f"{item['name']:<20} ${item['price']:>6.2f} × {item['quantity']}\n"

        receipt += "───────────────────────────────\n"
        receipt += f"Subtotal:              ${r['subtotal']:>7.2f}\n"

        if r['discount'] > 0:
            receipt += f"Discount:              -${r['discount']:>7.2f}\n"

        if r['points_redeemed'] > 0:
            receipt += f"Points Redeemed:        {r['points_redeemed']}\n"
            receipt += f"Remaining Points:       {r['remaining_points']}\n"

        receipt += f"GST (15%):             ${r['gst']:>7.2f}\n"
        receipt += f"TOTAL:                 ${r['total']:>7.2f}\n"

        receipt += "───────────────────────────────\n"
        receipt += f"Payment: {r['payment_method']}\n"
        receipt += "═══════════════════════════════\n"
        receipt += "     THANK YOU FOR SHOPPING!\n"
        receipt += "        HAVE A GREAT DAY!\n"
        receipt += "═══════════════════════════════"

        return receipt

    def on_close(self):
        """Handle window close"""
        self.destroy()

# helper to add product (auto-added by fixer)
def _auto_add_product_helper(name, sku, price, stock, description=''):
    pid = 'P' + str(int(datetime.now().timestamp()) % 100000)
    return db.add_product(pid, sku, name, description, price, stock)


class AddProductPage(bs.Toplevel):
    def __init__(self, parent, logged_in_user):
        super().__init__(parent)
        self.parent = parent
        self.logged_in_user = logged_in_user

        self.title("➕ Add New Product - Fit NZ")
        self.geometry("420x380")
        self.resizable(False, False)
        self.transient(parent)

        # Use ONLY grid inside this frame
        container = ttk.Frame(self, padding=25)
        container.grid(row=0, column=0, sticky="nsew")

        ttk.Label(container, text="➕ Add Product", font=("Segoe UI", 18, "bold"),
                  bootstyle="primary").grid(row=0, column=0, columnspan=2, pady=(0, 20))

        labels = ["Product ID:", "Product Name:", "Price:", "Stock:"]
        self.entries = {}

        for i, label in enumerate(labels):
            ttk.Label(container, text=label, font=("Segoe UI", 10, "bold")).grid(
                row=i + 1, column=0, sticky="w", pady=10
            )
            entry = ttk.Entry(container, font=("Segoe UI", 10), width=25)
            entry.grid(row=i + 1, column=1, sticky="ew", padx=(10, 0), ipady=5)
            self.entries[label] = entry

        container.grid_columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(container)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(25, 0), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ttk.Button(btn_frame, text="💾 Save Product", bootstyle="success",
                   command=self.save_product).grid(row=0, column=0, padx=5, ipady=8, sticky="ew")

        ttk.Button(btn_frame, text="Cancel", bootstyle="secondary-outline",
                   command=self.destroy).grid(row=0, column=1, padx=5, ipady=8, sticky="ew")

    def save_product(self):
        pid = self.entries["Product ID:"].get()
        name = self.entries["Product Name:"].get()
        price = self.entries["Price:"].get()
        stock = self.entries["Stock:"].get()

        if not all([pid, name, price, stock]):
            Messagebox.show_error("Please fill all fields.", "Missing Data", parent=self)
            return

        try:
            price = float(price)
            stock = int(stock)
        except:
            Messagebox.show_error("Price must be a number and stock must be integer.", "Invalid Input", parent=self)
            return

        new_product = db.add_product(pid, name, price, stock)

        if new_product:
            Messagebox.show_info("Product added successfully.", "Success", parent=self)
            self.parent.load_products()
            self.destroy()
        else:
            Messagebox.show_error("Failed to add product. Product ID may already exist.", "Error", parent=self)



class EditProductPage(bs.Toplevel):
    """Window to edit an existing product"""

    def __init__(self, parent, product_id):
        super().__init__(parent)

        self.parent = parent
        self.product_id = product_id
        self.title("✏️ Edit Product - Fit NZ")
        self.geometry("450x420")
        self.resizable(False, False)
        self.transient(parent)

        # Fetch product
        self.product = db.get_product_by_id(product_id)
        if not self.product:
            Messagebox.show_error("Product not found!", "Error", parent=self)
            self.destroy()
            return

        # OUTER FRAME (pack)
        outer = ttk.Frame(self, padding=25)
        outer.pack(expand=True, fill="both")

        ttk.Label(
            outer,
            text="✏️ Edit Product",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).pack(pady=(0, 20))

        # INNER FRAME (grid)
        form = ttk.Frame(outer)
        form.pack(fill="both", expand=True)

        # --- PRODUCT NAME ---
        ttk.Label(form, text="Product Name:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=10)
        self.name_entry = ttk.Entry(form, font=("Segoe UI", 10), width=25)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=10, ipady=6)
        self.name_entry.insert(0, self.product.name)

        # --- PRICE ---
        ttk.Label(form, text="Price:", font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=10)
        self.price_entry = ttk.Entry(form, font=("Segoe UI", 10), width=25)
        self.price_entry.grid(row=1, column=1, sticky="ew", pady=10, ipady=6)
        self.price_entry.insert(0, str(self.product.price))

        # --- STOCK ---
        ttk.Label(form, text="Stock:", font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=10)
        self.stock_entry = ttk.Entry(form, font=("Segoe UI", 10), width=25)
        self.stock_entry.grid(row=2, column=1, sticky="ew", pady=10, ipady=6)
        self.stock_entry.insert(0, str(self.product.stock))

        form.grid_columnconfigure(1, weight=1)

        # BUTTON FRAME (pack)
        btn_frame = ttk.Frame(outer)
        btn_frame.pack(pady=(25, 0))

        ttk.Button(
            btn_frame,
            text="💾 Save Changes",
            bootstyle="success",
            command=self.save_changes,
            width=18
        ).grid(row=0, column=0, padx=5, ipady=8)

        ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="secondary-outline",
            command=self.destroy,
            width=18
        ).grid(row=0, column=1, padx=5, ipady=8)

    def save_changes(self):
        """Save edited product information"""
        name = self.name_entry.get().strip()
        price = self.price_entry.get().strip()
        stock = self.stock_entry.get().strip()

        if not name or not price or not stock:
            Messagebox.show_error("All fields are required.", "Missing Data", parent=self)
            return

        try:
            price = float(price)
            stock = int(stock)
        except:
            Messagebox.show_error("Enter valid numeric values for price and stock.", "Invalid Input", parent=self)
            return

        updated = db.update_product(self.product_id, name, price, stock)

        if updated:
            Messagebox.show_info("Product updated successfully.", "Success", parent=self)
            self.parent.load_products()
            self.destroy()
        else:
            Messagebox.show_error("Failed to update product.", "Error", parent=self)


class CustomerOrderHistoryPage(bs.Toplevel):
    """
    Shows order history for logged-in customers
    """
    def __init__(self, parent, customer_obj):
        super().__init__(parent)

        self.parent = parent
        self.customer = customer_obj

        self.title("📦 Your Orders - Fit NZ")
        self.geometry("850x550")
        self.resizable(True, True)
        self.transient(parent)

        main = ttk.Frame(self, padding=20)
        main.pack(expand=True, fill="both")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        ttk.Label(
            main,
            text="📦 Order History",
            font=("Segoe UI", 20, "bold"),
            bootstyle="primary"
        ).grid(row=0, column=0, sticky="w")

        # Orders Table -------------------------------------------------------
        table_frame = ttk.Labelframe(
            main, text="Your Orders", padding=10, bootstyle="info"
        )
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("Order ID", "Date", "Total", "GST", "Delivery")
        self.order_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            bootstyle="info"
        )

        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, anchor="center", width=150)

        self.order_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.order_tree.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.order_tree.configure(yscrollcommand=scrollbar.set)

        # Load customer orders
        self.load_orders()

        # Bottom ------------------------------------------------------------
        bottom = ttk.Frame(main)
        bottom.grid(row=2, column=0, sticky="ew", pady=(20, 0))

        ttk.Button(
            bottom,
            text="🔍 View Order Items",
            bootstyle="primary",
            command=self.view_order_items
        ).pack(side="left")

        ttk.Button(
            bottom,
            text="← Back",
            bootstyle="secondary-outline",
            command=self.destroy
        ).pack(side="right")

    # ----------------------------------------------------------------------
    def load_orders(self):
        for row in self.order_tree.get_children():
            self.order_tree.delete(row)

        orders = db.get_orders_by_customer(self.customer._customer_id)

        if not orders:
            return

        for o in orders:
            self.order_tree.insert(
                "",
                "end",
                iid=str(o["id"]),
                values=(
                    o["id"],
                    o["datetime"],
                    f"${o['total']:.2f}",
                    f"${o['gst']:.2f}",
                    o["delivery_date"]
                )
            )

    # ----------------------------------------------------------------------
    def view_order_items(self):
        selected = self.order_tree.focus()
        if not selected:
            Messagebox.show_warning("Select an order first.", "No Selection", parent=self)
            return

        details = db.get_sale_details(selected)

        if not details:
            Messagebox.show_error("No order items found.", "Error", parent=self)
            return

        text = f"🧾 Order ID: {selected}\n\n"

        for d in details:
            text += f"{d['name']}  x{d['qty']}  —  ${d['line_total']:.2f}\n"

        Messagebox.show_info(text, "Order Items", parent=self)



        
