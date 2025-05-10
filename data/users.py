import json
import os

FILE_PATH = "data/users.json"

def load_users():
    if not os.path.exists(FILE_PATH):
        return []
    with open(FILE_PATH, "r") as f:
        return json.load(f)

def save_users(user_list):
    with open(FILE_PATH, "w") as f:
        json.dump(user_list, f)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)
        return True
    return False