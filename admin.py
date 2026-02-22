from telegram import Update
from telegram.ext import ContextTypes
from db import movies_col
from config import ADMIN_ID

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Only admin can use this.")

    if len(context.args) < 4:
        return await update.message.reply_text(
            "Usage:\n/add <name> <episode> <quality> <link>\n"
            "Example:\n/add kgf 1 720p https://t.me/yourchannel/12"
        )

    name = context.args[0].lower()
    episode = context.args[1]
    quality = context.args[2]
    link = context.args[3]

    movies_col.insert_one({
        "name": name,
        "episode": episode,
        "quality": quality,
        "link": link
    })

    await update.message.reply_text(f"✅ Added: {name} | Ep {episode} | {quality}")
