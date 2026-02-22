import os
import asyncio
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from utils.file_id_logger import file_id_logger
from db import movies_col, users_col
from admin import add_movie

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_USERNAME = "@RivoBots"  # change this

# --- GLOBAL TEMP MAP (chat wise) ---
FILE_MAP = {}  # { chat_id: { "1": "FILE_ID", "2": "FILE_ID2" } }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send movie/series name to search.")

async def is_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def force_join(update: Update):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("🔁 Check Joined", callback_data="check_join")]
    ])
    await update.message.reply_text("❌ First join our update channel!", reply_markup=kb)

async def check_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if await is_joined(update, context):
        await q.message.edit_text("✅ Joined! Now send movie name.")
    else:
        await q.message.edit_text("❌ Not joined yet!", reply_markup=q.message.reply_markup)

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(update, context):
        await force_join(update)
        return

    query = update.message.text.lower()
    searching_msg = await update.message.reply_text(f"🔎 Searching: {query}")
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    await asyncio.sleep(1.5)

    results = movies_col.find({"keywords": {"$regex": re.escape(query), "$options": "i"}})

    text = f"Results for: {query}\n\n"
    buttons = []

    found = False
    FILE_MAP[update.effective_chat.id] = {}
    idx = 1

    for m in results:
        for f in m["files"]:
            found = True
            text += f"🍿 {m['title']} – {f['quality']}\n"
            short_id = str(idx)
            FILE_MAP[update.effective_chat.id][short_id] = f["file_id"]

            buttons.append([
                InlineKeyboardButton(f"{f['quality']}", callback_data=f"send|{short_id}")
            ])
            idx += 1

    if not found:
        await searching_msg.edit_text("❌ No results found. Check spelling.")
    else:
        await searching_msg.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    try:
        await update.message.delete()
    except:
        pass

async def send_file_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, short_id = q.data.split("|", 1)
    chat_id = q.message.chat_id

    file_id = FILE_MAP.get(chat_id, {}).get(short_id)

    if not file_id:
        await q.message.reply_text("❌ File expired. Search again.")
        return

    await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_DOCUMENT)
    await context.bot.send_document(chat_id, file_id)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_movie))
    app.add_handler(CallbackQueryHandler(check_join_cb, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(send_file_cb, pattern=r"^send\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie))

    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), lambda u, c: file_id_logger(u, c, ADMIN_ID)))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
