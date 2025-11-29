# File: FITNZ/models/employee.py
from .user import User

# ===============================================
# Code Owner: Umang (US: As an Employee, view the full product list)
# This class models the base staff structure, supporting all employee-type roles.
# ===============================================

class Employee(User):
    """Represents an employee with a specific role."""
    def __init__(self, employee_id: str, name: str, role: str, username: str, password: str):
        super().__init__(username, password)
        # Roles can be 'Developer', 'Manager', 'Employee', 'Owner'
        self.employee_id = employee_id
        self.name = name
        self.role = role

    def __str__(self):
        return f"{self.name} ({self.role})"