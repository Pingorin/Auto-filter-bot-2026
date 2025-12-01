from pyrogram import Client, filters
from pyrogram.types import Message
from database.users_chats_db import db # Pichli file se db instance import karein
from script import Script # Messages import karein

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    """/start command ko handle karein aur user tracking shuru karein."""
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # 1. User check karein
    if not await db.is_user_exist(user_id):
        # Agar naya user hai toh database mein add karein
        await db.add_user(user_id, user_name)
        print(f"Naya User Added: {user_name} ({user_id})")

    # 2. Welcome message reply karein
    await message.reply_text(
        Script.START_TXT.format(
            mention=message.from_user.mention, # User ka mention (link)
            id=user_id
        ),
        disable_web_page_preview=True
    )
