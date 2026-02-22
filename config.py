import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MONGO_URI = os.getenv("MONGO_URI")
FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "").replace("@", "")
