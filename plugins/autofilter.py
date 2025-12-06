from pyrogram import Client, filters
from database.ia_filterdb import Media
from utils.utils import btn_parser
from pyrogram.types import InlineKeyboardMarkup

# 1. Text Message Listener
@Client.on_message(filters.text & filters.incoming & ~filters.command(["start", "index"]))
async def auto_filter(client, message):
    
    query = message.text
    if len(query) < 3:
        return # Agar 3 letters se chhota hai to ignore karo
    
    # Database search
    files = await Media.get_search_results(query)
    
    if not files:
        # Agar file nahi mili
        # await message.reply("Koi file nahi mili 😕") # Ise ON mat karna warna spam hoga
        return

    # Buttons banao
    buttons = btn_parser(files)
    
    await message.reply_text(
        f"Found {len(files)} results for **{query}**:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 2. Button Callback (Jab user file button dabaye)
@Client.on_callback_query(filters.regex(r"^sendfile#"))
async def send_file_handler(client, callback_query):
    
    file_id = callback_query.data.split("#")[1]
    
    try:
        await callback_query.message.reply_document(document=file_id)
        await callback_query.answer() # Loading animation band karo
    except Exception as e:
        await callback_query.answer("File bhej nahi pa raha (Copyright/Error)", show_alert=True)
