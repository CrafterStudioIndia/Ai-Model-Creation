import json
import os

def save_unknown_query(user_input):
    with open("new_queries.txt", "a", encoding="utf-8") as f:
        f.write(user_input + "\n")
