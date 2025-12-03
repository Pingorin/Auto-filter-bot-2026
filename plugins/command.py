# plugins/command.py
from pyrogram import Client, filters
from pyrogram.types import Message
from database.ia_filterdb import set_new_skip_id

# --- /index command ---
@Client.on_message(filters.command("index") & filters.private)
async def index_setup_command(client: Client, message: Message):
    """
    Handles the /index command, guiding the user to start the process.
    """
    # Authorization check: ADMINS list bot.py se client object mein attached hai.
    if message.from_user.id not in client.ADMINS:
        return await message.reply_text("🚫 **Access Denied.** Only bot admins can initiate the indexing process.")
        
    intro_text = (
        "**🚀 Indexing Process Shuru Karein**\n\n"
        "Kripya woh channel select karein jise aap index karna chahte hain, aur phir **uss channel ka sabse aakhri (latest) message** yahan forward karein.\n\n"
        "**💡 Yeh Kaise Kaam Karega:**\n"
        "1. Jo message aap forward karenge, uski ID (`last_msg_id`) tak messages index kiye jayenge (purane messages ki taraf).\n"
        "2. Bot apne aap check karega ki woh uss channel mein Admin hai ya nahi.\n"
        "3. Forward karne ke baad, indexing shuru ho jayegi aur aapko progress updates milenge."
    )
    await message.reply_text(intro_text)


# --- /setskip command --- (Existing Logic)
@Client.on_message(filters.command("setskip") & filters.private)
async def set_skip_id_command(client: Client, message: Message):
    """
    Sets the starting message ID (skip ID) for indexing.
    """
    if message.from_user.id not in client.ADMINS:
        return await message.reply_text("🚫 **Access Denied.** Only bot admins can use this command.")

    try:
        skip_id = int(message.text.split(None, 1)[1])
    except:
        return await message.reply_text("Usage: `/setskip <message_id>`")

    await set_new_skip_id(skip_id)
    await message.reply_text(f"✅ New skip ID set to **{skip_id}**.\nIndexing will start from this message ID.")
