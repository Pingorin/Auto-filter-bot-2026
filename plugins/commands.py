from pyrogram import Client, filters
from database.users_chats_db import db

@Client.on_message(filters.command("start"))
async def start(client, message):
    # Database me user add karo
    await db.add_user(message.from_user.id)
    
    await message.reply_text(
        f"Hello {message.from_user.mention}! 👋\n\nMain ek Auto Filter Bot hu. Abhi main naya bana hu!"
    )
