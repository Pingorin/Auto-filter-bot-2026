from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from script import script, temp  # Importing script and temp

# Mock function for status (replace with your actual DB logic)
def get_status():
    return "Free"

# --- NEW: @Client.on_message Handler ---
@Client.on_message(filters.command("start") & filters.incoming)
async def start_command(client: Client, message: Message):
    # Fetch Bot Username if not already set
    if not temp.U_NAME:
        bot_info = await client.get_me()
        temp.U_NAME = bot_info.username

    # Case 1: Normal /start (No arguments)
    if len(message.command) != 2:
        buttons = [
            [
                InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ⇆', url=f'http://t.me/{temp.U_NAME}?startgroup=start')
            ],
            [
                InlineKeyboardButton('⚙ ꜰᴇᴀᴛᴜʀᴇs', callback_data='features'),
                InlineKeyboardButton('💸 ᴘʀᴇᴍɪᴜᴍ', callback_data='buy_premium')
            ],
            [
                InlineKeyboardButton('🚫 ᴇᴀʀɴ ᴍᴏɴᴇʏ ᴡɪᴛʜ ʙᴏᴛ 🚫', callback_data='earn')
            ]
        ]   
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await message.reply_text(
            script.START_TXT.format(message.from_user.mention, get_status(), message.from_user.id),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return

    # Case 2: Deep Linking (argument provided)
    argument = message.command[1]
    await message.reply_text(f"Bot started with argument: {argument}")
