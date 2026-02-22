import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URL")
if not MONGO_URI:
    raise ValueError("MONGO_URL env missing!")

client = MongoClient(MONGO_URI)
db = client["moviebot"]

movies_col = db["movies"]
users_col = db["users"]
