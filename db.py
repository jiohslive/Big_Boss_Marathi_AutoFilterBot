import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URL")

if not MONGO_URI:
    raise ValueError("MONGO_URL is not set in env")

mongo = MongoClient(MONGO_URI)
db = mongo["autofilter"]
movies_col = db["movies"]
