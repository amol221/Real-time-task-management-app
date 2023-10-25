# User class to represent a user with attributes for ID, username, and password.
class User:
    def __init__(self, username, password, _id=None):
        self.id = _id
        self.username = username
        self.password = password

# Task class to represent individual tasks with title, description, and associated user ID.

class Task:
    def __init__(self, title, description, user_id, _id=None):
        self.id = _id
        self.title = title
        self.description = description
        self.user_id = user_id

