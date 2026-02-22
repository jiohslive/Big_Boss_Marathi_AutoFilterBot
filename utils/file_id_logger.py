async def file_id_logger(update, context, ADMIN_ID):
    msg = update.message
    if not msg:
        return

    if msg.video or msg.document:
        file = msg.video or msg.document
        await context.bot.send_message(
            ADMIN_ID,
            f"📁 File ID:\n<code>{file.file_id}</code>",
            parse_mode="HTML"
        )
