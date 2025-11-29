# File: FITNZPROJECT/models/user.py

class User:
    def __init__(self, username, password):
        self.username = username
        self._password = password

    def check_password(self, password_to_check):
        return self._password == password_to_check