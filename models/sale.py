# File: FITNZPROJECT/models/sale.py
from datetime import datetime
from typing import List
from .customer import Customer
from .employee import Employee
from .product import Product

class Sale:
    def __init__(self, sale_id: int, customer: Customer, employee: Employee, items: List[Product]):
        self.sale_id = sale_id
        self.customer = customer
        self.employee = employee
        self.items = items
        self.transaction_time = datetime.now()
        self.total_amount = sum(item.price for item in self.items)