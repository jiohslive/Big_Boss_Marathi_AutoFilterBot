from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram import Update
from config import BOT_TOKEN, FORCE_SUB_CHANNEL
from admin import add_movie
from filters import search_movie, send_movie
from force_sub import is_joined, join_markup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(update, context, FORCE_SUB_CHANNEL):
        return await update.message.reply_text(
            "🔒 Join channel to use bot!",
            reply_markup=join_markup(FORCE_SUB_CHANNEL)
        )
    await update.message.reply_text("🎬 Movie name type kara")

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if await is_joined(update, context, FORCE_SUB_CHANNEL):
        await q.edit_message_text("✅ Now send movie name")
    else:
        await q.answer("❌ Join first", show_alert=True)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_movie))
    app.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(send_movie, pattern="^get\\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie))

    print("🤖 Multi-file Auto Filter Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
