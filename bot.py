import os
import logging
from datetime import datetime, timedelta

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

from pymongo import MongoClient

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MONGO_URL = os.getenv("MONGO_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = MongoClient(MONGO_URL)
db = client["rivo_bots"]
movies_col = db["movies"]
users_col = db["users"]

SHOW_NAME = "Bigg Boss Marathi"

# ================= HELPERS =================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_show():
    show = movies_col.find_one({"show": SHOW_NAME})
    if not show:
        movies_col.insert_one({
            "show": SHOW_NAME,
            "seasons": {"6": {"episodes": {}}}
        })
        show = movies_col.find_one({"show": SHOW_NAME})
    return show

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users_col.update_one(
        {"_id": user.id},
        {"$set": {"name": user.full_name, "joined": datetime.utcnow()}},
        upsert=True
    )

    buttons = [
        [InlineKeyboardButton("📺 Bigg Boss Marathi S6", callback_data="open_s6")],
    ]

    await update.message.reply_text(
        "👋 Welcome to *Rivo Bots*\n\nSelect a category:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

# ================= OPEN SEASON =================
async def open_s6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    show = get_show()
    episodes = show["seasons"]["6"]["episodes"]

    if not episodes:
        await q.message.reply_text("❌ No episodes uploaded yet.")
        return

    buttons = []
    for ep in sorted(episodes.keys(), key=lambda x: int(x)):
        buttons.append([InlineKeyboardButton(f"S6E{ep}", callback_data=f"ep|{ep}")])

    await q.message.reply_text(
        "📂 *Select Episode:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

# ================= EPISODE =================
async def episode_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    ep = q.data.split("|")[1]
    show = get_show()
    files = show["seasons"]["6"]["episodes"].get(ep, [])

    if not files:
        await q.message.reply_text("❌ Files not found.")
        return

    context.user_data["files_map"] = {str(i): f["file_id"] for i, f in enumerate(files)}

    buttons = [
        [InlineKeyboardButton(f["quality"], callback_data=f"send|{i}")]
        for i, f in enumerate(files)
    ]

    await q.message.reply_text(
        f"🎬 *S6E{ep}* – Choose quality:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

async def send_file_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    key = q.data.split("|")[1]
    file_id = context.user_data.get("files_map", {}).get(key)

    if not file_id:
        await q.message.reply_text("❌ File expired. Open episode again.")
        return

    await context.bot.send_chat_action(q.message.chat_id, ChatAction.UPLOAD_DOCUMENT)
    await context.bot.send_document(q.message.chat_id, file_id)

# ================= ADMIN PANEL =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    buttons = [
        [InlineKeyboardButton("➕ Add Episode", callback_data="admin_add_ep")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
    ]

    await update.message.reply_text(
        "🔐 *Admin Dashboard*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    users = users_col.count_documents({})
    show = get_show()
    total_eps = len(show["seasons"]["6"]["episodes"])

    await q.message.reply_text(
        f"📊 *Stats*\n\n👥 Users: {users}\n🎬 Episodes: {total_eps}",
        parse_mode=ParseMode.MARKDOWN
    )

# ================= ADD EPISODE =================
async def admin_add_ep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.callback_query.answer()
    context.user_data["add_mode"] = True

    await update.callback_query.message.reply_text(
        "➕ Send episode like:\n\n"
        "`/add 105|1080p|<file_id>`",
        parse_mode=ParseMode.MARKDOWN
    )

async def add_episode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    try:
        _, data = update.message.text.split(" ", 1)
        ep, quality, file_id = data.split("|")

        show = get_show()
        movies_col.update_one(
            {"show": SHOW_NAME},
            {"$push": {f"seasons.6.episodes.{ep}": {
                "quality": quality,
                "file_id": file_id
            }}}
        )

        await update.message.reply_text(f"✅ Added S6E{ep} [{quality}]")

    except Exception as e:
        await update.message.reply_text("❌ Format error.\nUse: /add 105|1080p|<file_id>")

# ================= BROADCAST =================
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = update.message.text.replace("/broadcast", "").strip()
    if not msg:
        await update.message.reply_text("❌ /broadcast <message>")
        return

    users = users_col.find({})
    sent = 0

    for u in users:
        try:
            await context.bot.send_message(u["_id"], msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users")

# ================= ERROR =================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception:", exc_info=context.error)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add", add_episode_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))

    app.add_handler(CallbackQueryHandler(open_s6, pattern="^open_s6$"))
    app.add_handler(CallbackQueryHandler(episode_cb, pattern="^ep\\|"))
    app.add_handler(CallbackQueryHandler(send_file_cb, pattern="^send\\|"))
    app.add_handler(CallbackQueryHandler(admin_add_ep, pattern="^admin_add_ep$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))

    app.add_error_handler(error_handler)

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
