from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from script import START_TXT, temp 

# --- IMPORTANT FIX HERE ---
# Import from database.py instead of bot.py to prevent the "Event loop" error
from database import groups_collection 

# Mock function for status 
def get_status():
    return "Free"

# --- Helper Function: Save Group to DB ---
async def add_group_to_db(group_id, group_name, added_by_user_id):
    try:
        await groups_collection.update_one(
            {"_id": group_id},
            {
                "$set": {
                    "group_name": group_name,
                    "added_by": added_by_user_id,
                    "is_active": True
                }
            },
            upsert=True
        )
        print(f"Saved Group: {group_name} ({group_id})")
    except Exception as e:
        print(f"Error saving group: {e}")

# 1. /start Command Handler
@Client.on_message(filters.command("start") & filters.incoming)
async def start_command(client: Client, message: Message):
    if not temp.U_NAME:
        bot_info = await client.get_me()
        temp.U_NAME = bot_info.username

    if len(message.command) > 1:
        argument = message.command[1]
        await message.reply_text(f"Bot started with argument: {argument}")
        return

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
        START_TXT.format(message.from_user.mention, get_status(), message.from_user.id),
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
    )

# 2. Callback Handlers
@Client.on_callback_query(filters.regex("features"))
async def features_callback(client, callback_query):
    await callback_query.answer("Features section coming soon!", show_alert=True)

@Client.on_callback_query(filters.regex("buy_premium"))
async def premium_callback(client, callback_query):
    await callback_query.answer("Premium section coming soon!", show_alert=True)

@Client.on_callback_query(filters.regex("earn"))
async def earn_callback(client, callback_query):
    await callback_query.answer("Earning section coming soon!", show_alert=True)

# 3. New Chat Members Handler
@Client.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    bot_id = (await client.get_me()).id
    for member in message.new_chat_members:
        if member.id == bot_id:
            group_id = message.chat.id
            group_name = message.chat.title
            added_by = message.from_user.id if message.from_user else None
            await add_group_to_db(group_id, group_name, added_by)
            await message.reply(f"Thanks for adding me to **{group_name}**!")
