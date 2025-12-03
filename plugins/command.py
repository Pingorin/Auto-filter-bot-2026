# plugins/command.py
from pyrogram import Client, filters
from pyrogram.types import Message
from database.ia_filterdb import set_new_skip_id

# --- /setskip command ---
@Client.on_message(filters.command("setskip") & filters.private)
async def set_skip_id_command(client: Client, message: Message):
    # Authorization check is crucial, assuming ADMINS is imported or accessible
    # from config.
    if message.from_user.id not in client.ADMINS:
        return await message.reply_text("You are not authorized to use this command.")

    try:
        skip_id = int(message.text.split(None, 1)[1])
    except:
        return await message.reply_text("Usage: /setskip <message_id>")

    await set_new_skip_id(skip_id)
    await message.reply_text(f"✅ New skip ID set to **{skip_id}**.\nIndexing will start from this message ID.")
