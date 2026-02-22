from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from db import movies_col, users_col

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, ADMIN_ID):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Episode", callback_data="admin|add_ep")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin|stats")],
        [InlineKeyboardButton("🗑 Remove Episode", callback_data="admin|rm_ep")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin|bc")]
    ])
    await update.message.reply_text("🧑‍💻 Admin Dashboard", reply_markup=kb)

async def admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE, ADMIN_ID):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    action = q.data.split("|")[1]

    if action == "stats":
        total_users = users_col.count_documents({})
        show = movies_col.find_one({"show": "Bigg Boss Marathi"})
        total_eps = len(show["seasons"]["6"]["episodes"])
        await q.message.edit_text(f"📊 Stats\n\n👥 Users: {total_users}\n🎬 Episodes: {total_eps}")

    elif action == "add_ep":
        await q.message.edit_text("➕ Send:\n/add 105|1080p|FILE_ID")

    elif action == "rm_ep":
        await q.message.edit_text("🗑 Send:\n/remove 105")

    elif action == "bc":
        context.user_data["broadcast"] = True
        await q.message.edit_text("📢 Send broadcast message now.")

async def add_episode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, ADMIN_ID):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        _, data = update.message.text.split(" ", 1)
        ep, quality, file_id = data.split("|")

        movies_col.update_one(
            {"show": "Bigg Boss Marathi"},
            {"$set": {f"seasons.6.episodes.{ep}": [{"quality": quality, "file_id": file_id}]}}
        )
        await update.message.reply_text(f"✅ Episode {ep} added ({quality})")

    except:
        await update.message.reply_text("❌ Format: /add 105|1080p|FILE_ID")

async def remove_episode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, ADMIN_ID):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        ep = update.message.text.split(" ", 1)[1]
        movies_col.update_one(
            {"show": "Bigg Boss Marathi"},
            {"$unset": {f"seasons.6.episodes.{ep}": ""}}
        )
        await update.message.reply_text(f"🗑 Episode {ep} removed")
    except:
        await update.message.reply_text("❌ Format: /remove 105")
