import os
import json
import traceback

USERS_FILE = "data/users.json"

class UserManager:
    def __init__(self):
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # If users file doesn't exist, create with default users
            if not os.path.exists(USERS_FILE):
                default_users = [
                    {"username": "user1", "password": "password1"},
                    {"username": "user2", "password": "password2"},
                    {"username": "user3", "password": "password3"}
                ]
                with open(USERS_FILE, "w") as f:
                    json.dump(default_users, f, indent=2)
                print(f"[User] Created default users file")
        except Exception as e:
            print(f"[User] Error initializing user manager: {e}")
            print(traceback.format_exc())
    
    def get_all_users(self):
        """Get all registered users"""
        try:
            if not os.path.exists(USERS_FILE):
                with open(USERS_FILE, "w") as f:
                    json.dump([], f)
                return []
            
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
            return users
        except Exception as e:
            print(f"[User] Error reading users: {e}")
            print(traceback.format_exc())
            return []
    
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password"""
        try:
            users = self.get_all_users()
            
            for user in users:
                if user["username"] == username and user["password"] == password:
                    return True, user
            
            return False, "Invalid username or password"
        except Exception as e:
            print(f"[User] Authentication error: {e}")
            print(traceback.format_exc())
            return False, str(e)
    
    def get_user_orders(self, username, orders):
        """Filter orders to get only those belonging to a specific user"""
        return [order for order in orders if order.get("user") == username]