import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction, ParseMode
from db import movies_col

async def search_movie(update, context):
    msg = update.message
    query = msg.text.lower().strip()

    await context.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
    await asyncio.sleep(1)

    await msg.delete()

    results = list(movies_col.find({"name": {"$regex": query}}))

    if not results:
        return await context.bot.send_message(msg.chat.id, "❌ Movie not found")

    buttons = [
        [InlineKeyboardButton(f"Ep {r['episode']} | {r['quality']}", callback_data=f"get|{r['_id']}")]
        for r in results[:10]
    ]

    await context.bot.send_message(
        msg.chat.id,
        f"🎬 Results for: *{query}*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def send_movie(update, context):
    from bson import ObjectId

    query = update.callback_query
    await query.answer()

    _id = query.data.split("|")[1]
    movie = movies_col.find_one({"_id": ObjectId(_id)})

    if not movie:
        return await query.edit_message_text("❌ File not found")

    await query.message.reply_text(
        f"📥 *Download*\n\nEp: {movie['episode']}\nQuality: {movie['quality']}\n\n{movie['link']}",
        parse_mode=ParseMode.MARKDOWN
    )
