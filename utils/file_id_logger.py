from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

async def file_id_logger(update: Update, context: ContextTypes.DEFAULT_TYPE, ADMIN_ID: int):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.effective_message

    file_id = None
    file_type = None

    if msg.video:
        file_id = msg.video.file_id
        file_type = "VIDEO"
    elif msg.document:
        file_id = msg.document.file_id
        file_type = "DOCUMENT"
    elif msg.audio:
        file_id = msg.audio.file_id
        file_type = "AUDIO"
    elif msg.voice:
        file_id = msg.voice.file_id
        file_type = "VOICE"
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = "PHOTO"

    if file_id:
        text = (
            f"📦 <b>File Type:</b> {file_type}\n\n"
            f"🆔 <b>File ID:</b>\n"
            f"<code>{file_id}</code>\n\n"
            f"👉 Copy this file_id and use in /add command"
        )
        await msg.reply_text(text, parse_mode=ParseMode.HTML)
      
