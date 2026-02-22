from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["rivo_bots"]
movies_col = db["movies"]
users_col = db["users"]

# Init Bigg Boss Marathi if not exists
def init_show():
    if not movies_col.find_one({"show": "Bigg Boss Marathi"}):
        movies_col.insert_one({
            "show": "Bigg Boss Marathi",
            "seasons": {
                "6": {
                    "episodes": {}  # "105": [{"quality": "1080p", "file_id": "..."}]
                }
            }
        })

init_show()
