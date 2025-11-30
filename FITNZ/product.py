# File: FITNZ/models/product.py
# ===============================================
# Code Owner: Umang (US: Add a new product / Update the stock quantity)
# This class manages the definition and state of inventory items.
# ===============================================
class Product:
    """Represents a single product in the store's inventory."""
    def __init__(self, product_id: str, name: str, price: float, stock: int):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock = stock

    def update_stock(self, quantity: int):
        """Updates the stock level. Can be positive (adding stock) or negative (selling)."""
        if self.stock + quantity >= 0:
            self.stock += quantity
        else:
            print(f"Error: Not enough stock for {self.name}.")

    def __str__(self):
        """String representation for easy display."""
        return f"{self.name} - ${self.price:.2f} (Stock: {self.stock})"