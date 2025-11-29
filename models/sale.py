# File: FITNZ/models/sales.py

from datetime import datetime
from .customer import Customer
from .employee import Employee
from .product import Product
from typing import List


# ===============================================
# Code Owner: Sahil (US: Complete my purchase by providing payment details)
# This class models the overall transaction structure.
# ===============================================

class Sale:
    """Represents a single sales transaction."""
    def __init__(self, sale_id: int, customer: Customer, employee: Employee, items: List[Product]):
        self.sale_id = sale_id
        self.customer = customer
        self.employee = employee
        self.items = items
        self.transaction_time = datetime.now()
        self.total_amount = self._calculate_total()

    def _calculate_total(self) -> float:
        """Calculates the total cost of the sale, including discounts."""
        subtotal = sum(item.price for item in self.items)
        discount_rate = self.customer.get_discount_rate()
        discount_amount = subtotal * discount_rate
        final_total = subtotal - discount_amount
        return final_total

    def generate_receipt_info(self) -> dict:
        """Creates a dictionary of information needed for a receipt."""
        item_details = [{"name": item.name, "price": item.price} for item in self.items]
        receipt = {
            "sale_id": self.sale_id,
            "timestamp": self.transaction_time.strftime("%Y-%m-%d %H:%M:%S"),
            "customer_name": self.customer.get_name(),
            "employee_name": self.employee.name,
            "items": item_details,
            "subtotal": sum(item.price for item in self.items),
            "discount_applied": self.customer.get_discount_rate() * 100,
            "total": self.total_amount
        }
        return receipt
