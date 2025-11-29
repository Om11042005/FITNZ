# File: FITNZPROJECT/models/product.py

class Product:
    def __init__(self, product_id: str, name: str, price: float, stock: int, description: str, image_url: str):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock = stock
        self.description = description
        self.image_url = image_url

    def update_stock(self, quantity: int):
        if self.stock + quantity >= 0:
            self.stock += quantity
        else:
            print(f"Error: Not enough stock for {self.name}.")

    def __str__(self):
        return f"{self.name} - ${self.price:.2f} (Stock: {self.stock})"