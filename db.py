from pymongo import MongoClient
from config import MONGO_URI

mongo = MongoClient(MONGO_URI)
db = mongo["moviebot"]
movies_col = db["movies"]
