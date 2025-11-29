# File: FITNZPROJECT/models/employee.py

from .user import User

class Employee(User):
    def __init__(self, employee_id: str, name: str, role: str, username: str, password: str):
        super().__init__(username, password)
        self.employee_id = employee_id
        self.user_id = employee_id 
        self.name = name
        self.role = role

    def __str__(self):
        return f"{self.name} ({self.role})"