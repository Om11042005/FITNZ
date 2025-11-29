# File: FITNZ/models/user.py

# ===============================================
# Code Owner: Om (US: Register for a 'Customer' account and log in)
# This class defines the core identity structure for all authenticated users.
# ===============================================

class User:
    """A base class for any entity that can log into the system."""
    def __init__(self, username, password):
        self.username = username
        self._password = password # Encapsulated

    def check_password(self, password_to_check):
        """Checks if the provided password is correct."""
        return self._password == password_to_check
