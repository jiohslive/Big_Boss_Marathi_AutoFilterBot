from telegram import Update
from telegram.ext import ContextTypes
from db import movies_col

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /add <title>|<keywords comma>|<quality>|<file_id>")
        return

    try:
        data = " ".join(context.args)
        title, keywords, quality, file_id = data.split("|")

        keywords_list = [k.strip().lower() for k in keywords.split(",")]

        movie = movies_col.find_one({"title": title.strip()})

        if movie:
            movies_col.update_one(
                {"_id": movie["_id"]},
                {"$push": {"files": {"quality": quality.strip(), "file_id": file_id.strip()}}}
            )
        else:
            movies_col.insert_one({
                "title": title.strip(),
                "keywords": keywords_list,
                "files": [{"quality": quality.strip(), "file_id": file_id.strip()}]
            })

        await update.message.reply_text("✅ Movie/File added successfully!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
