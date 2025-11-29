# File: FITNZ/models/customer.py

from .user import User

class Customer(User):
    def __init__(self, customer_id: str, name: str, contact: str, username: str, password: str):
        super().__init__(username, password)
        self._customer_id = customer_id
        self._name = name
        self._contact = contact
        self.loyalty_points = 0
        self.transaction_history = []
        self.role = "Customer"
        self.membership_level = "Standard"
        self.address = "N/A" # Default address

    def get_discount_rate(self) -> float:
        return 0.0

    def get_name(self) -> str:
        return self._name
    
    def add_loyalty_points(self, points_to_add: int):
        self.loyalty_points += points_to_add

    def redeem_loyalty_points(self, points_to_redeem: int):
        if points_to_redeem <= self.loyalty_points:
            self.loyalty_points -= points_to_redeem
            return True
        return False
        
    def __str__(self):
        return f"ID: {self._customer_id}, Name: {self._name}, Membership: {self.membership_level}, Points: {self.loyalty_points}"

# --- ALL SUBCLASSES BELOW ARE NOW FIXED ---

class StudentMember(Customer):
    def __init__(self, customer: Customer):
        super().__init__(customer._customer_id, customer.get_name(), customer._contact, customer.username, customer._password)
        self.loyalty_points = customer.loyalty_points
        self.transaction_history = customer.transaction_history
        self.address = customer.address # <-- ADDED THIS FIX
        self.membership_level = "Student"
    
    def get_discount_rate(self) -> float:
        return 0.20 # 20% discount

class BronzeMember(Customer):
    def __init__(self, customer: Customer):
        super().__init__(customer._customer_id, customer.get_name(), customer._contact, customer.username, customer._password)
        self.loyalty_points = customer.loyalty_points
        self.transaction_history = customer.transaction_history
        self.address = customer.address # <-- ADDED THIS FIX
        self.membership_level = "Bronze"
    
    def get_discount_rate(self) -> float:
        return 0.05

class SilverMember(Customer):
    def __init__(self, customer: Customer):
        super().__init__(customer._customer_id, customer.get_name(), customer._contact, customer.username, customer._password)
        self.loyalty_points = customer.loyalty_points
        self.transaction_history = customer.transaction_history
        self.address = customer.address # <-- ADDED THIS FIX
        self.membership_level = "Silver"
    
    def get_discount_rate(self) -> float:
        return 0.10

class GoldMember(Customer):
    def __init__(self, customer: Customer):
        super().__init__(customer._customer_id, customer.get_name(), customer._contact, customer.username, customer._password)
        self.loyalty_points = customer.loyalty_points
        self.transaction_history = customer.transaction_history
        self.address = customer.address # <-- ADDED THIS FIX
        self.membership_level = "Gold"
    
    def get_discount_rate(self) -> float:
        return 0.15