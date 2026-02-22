import os, asyncio, re
from datetime import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

from db import movies_col, users_col
from utils.file_id_logger import file_id_logger
from admin import admin_panel, admin_cb, add_episode_cmd, remove_episode_cmd

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_USERNAME = "@RivoBots"

# ========== BASIC ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_col.update_one(
        {"user_id": update.effective_user.id},
        {"$set": {"user_id": update.effective_user.id}},
        upsert=True
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Bigg Boss Marathi S6", callback_data="cat|s6")]
    ])
    await update.message.reply_text("👋 Welcome! Choose category:", reply_markup=kb)

async def is_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        m = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

async def force_join(msg):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("🔁 Check Joined", callback_data="check_join")]
    ])
    await msg.reply_text("❌ First join channel!", reply_markup=kb)

async def check_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if await is_joined(update, context):
        await q.message.edit_text("✅ Joined! Now search episode number.")
    else:
        await q.message.edit_text("❌ Not joined yet!", reply_markup=q.message.reply_markup)

# ========== CATEGORY + PAGINATION ==========
async def category_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not await is_joined(update, context):
        await force_join(q.message)
        return

    show = movies_col.find_one({"show": "Bigg Boss Marathi"})
    eps = sorted(show["seasons"]["6"]["episodes"].keys(), key=int)
    context.user_data["eps"] = eps
    context.user_data["page"] = 0

    await show_page(q.message, context)

async def show_page(msg, context):
    eps = context.user_data["eps"]
    page = context.user_data["page"]

    per_page = 10
    start = page * per_page
    chunk = eps[start:start+per_page]

    buttons = [[InlineKeyboardButton(f"S6E{e}", callback_data=f"ep|{e}")] for e in chunk]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅ Prev", callback_data="nav|prev"))
    if start + per_page < len(eps):
        nav.append(InlineKeyboardButton("Next ➡", callback_data="nav|next"))
    if nav:
        buttons.append(nav)

    await msg.edit_text("📂 Bigg Boss Marathi Season 6 Episodes:", reply_markup=InlineKeyboardMarkup(buttons))

async def nav_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data.endswith("next"):
        context.user_data["page"] += 1
    else:
        context.user_data["page"] -= 1

    await show_page(q.message, context)

# ========== EPISODE SEND ==========
async def episode_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ep = q.data.split("|")[1]

    show = movies_col.find_one({"show": "Bigg Boss Marathi"})
    files = show["seasons"]["6"]["episodes"].get(ep)

    buttons = [
        [InlineKeyboardButton(f["quality"], callback_data=f"send|{f['file_id']}")]
        for f in files
    ]
    await q.message.reply_text(f"🎬 S6E{ep} – Choose quality:", reply_markup=InlineKeyboardMarkup(buttons))

async def send_file_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    file_id = q.data.split("|")[1]

    await context.bot.send_chat_action(q.message.chat_id, ChatAction.UPLOAD_DOCUMENT)
    await context.bot.send_document(q.message.chat_id, file_id)

# ========== AUTO SUGGEST ==========
async def auto_suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(update, context):
        await force_join(update.message)
        return

    text = update.message.text.strip()
    if not text.isdigit():
        return

    show = movies_col.find_one({"show": "Bigg Boss Marathi"})
    eps = show["seasons"]["6"]["episodes"].keys()
    sug = [e for e in eps if e.startswith(text)]

    if not sug:
        return

    buttons = [[InlineKeyboardButton(f"S6E{e}", callback_data=f"ep|{e}")] for e in sug[:10]]
    await update.message.reply_text("Did you mean 👇", reply_markup=InlineKeyboardMarkup(buttons))

# ========== DAILY AUTO POST ==========
async def daily_post(context: ContextTypes.DEFAULT_TYPE):
    show = movies_col.find_one({"show": "Bigg Boss Marathi"})
    eps = show["seasons"]["6"]["episodes"]
    if not eps:
        return

    last_ep = sorted(eps.keys(), key=int)[-1]
    file_id = eps[last_ep][0]["file_id"]

    await context.bot.send_document(
        chat_id=CHANNEL_USERNAME,
        document=file_id,
        caption=f"🔥 Today Episode: Bigg Boss Marathi S6E{last_ep}"
    )

# ========== MAIN ==========
from telegram.ext import Application, ApplicationBuilder
from telegram.ext import JobQueue

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", lambda u, c: admin_panel(u, c, ADMIN_ID)))
    app.add_handler(CommandHandler("add", lambda u, c: add_episode_cmd(u, c, ADMIN_ID)))
    app.add_handler(CommandHandler("remove", lambda u, c: remove_episode_cmd(u, c, ADMIN_ID)))

    app.add_handler(CallbackQueryHandler(check_join_cb, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(category_cb, pattern=r"^cat\|"))
    app.add_handler(CallbackQueryHandler(nav_cb, pattern=r"^nav\|"))
    app.add_handler(CallbackQueryHandler(episode_cb, pattern=r"^ep\|"))
    app.add_handler(CallbackQueryHandler(send_file_cb, pattern=r"^send\|"))
    app.add_handler(CallbackQueryHandler(lambda u, c: admin_cb(u, c, ADMIN_ID), pattern=r"^admin\|"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_suggest))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), lambda u, c: file_id_logger(u, c, ADMIN_ID)))

    # ✅ JobQueue safe setup
    if app.job_queue:
        app.job_queue.run_daily(daily_post, time=time(hour=21, minute=0))  # 9 PM

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
