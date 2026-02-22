from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def is_joined(update, context, channel):
    if not channel:
        return True
    try:
        member = await context.bot.get_chat_member(f"@{channel}", update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def join_markup(channel):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{channel}")],
        [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
    ])
