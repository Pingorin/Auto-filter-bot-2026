import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from database.ia_filterdb import Media
from info import ADMINS

@Client.on_message(filters.command("index") & filters.user(ADMINS))
async def index_channel(bot, message):
    
    # 1. Check Command
    if len(message.command) < 2:
        return await message.reply("Channel ID dijiye!\nExample: `/index -100123456789`")
    
    try:
        chat_id = int(message.command[1])
    except:
        return await message.reply("❌ Invalid Channel ID format!")

    msg = await message.reply("🧐 Connecting to Channel...")
    
    # 2. Check Permissions (Sabse Zaruri)
    try:
        chat = await bot.get_chat(chat_id)
        print(f"Connected to {chat.title}")
    except Exception as e:
        return await msg.edit(f"❌ Error: Main us channel ko access nahi kar pa raha.\n\nReason: `{e}`\n\nCheck karein ki main wahan **Admin** hoon aur **ID sahi** hai.")

    # 3. Start Indexing
    await msg.edit(f"✅ Connected to: **{chat.title}**\n📂 Files dhoondh raha hu...")
    
    total_files = 0
    duplicate = 0
    errors = 0

    try:
        async for message in bot.get_chat_history(chat_id):
            media = None
            if message.document:
                media = message.document
            elif message.video:
                media = message.video
            
            if media:
                try:
                    saved = await Media.save_file(media)
                    if saved:
                        total_files += 1
                    else:
                        duplicate += 1
                except Exception as e:
                    errors += 1
                    print(f"File Error: {e}")

                # Har 20 files par update
                if total_files % 20 == 0:
                    await msg.edit(f"Indexing {chat.title}...\nSaved: {total_files}\nDuplicates: {duplicate}")

    except Exception as e:
        await msg.edit(f"❌ Loop Error: Indexing beech mein ruk gayi.\nReason: `{e}`")
        return

    # 4. Final Result
    await msg.edit(f"✅ **Indexing Complete!**\n\n📂 Total Saved: {total_files}\n♻️ Duplicates: {duplicate}\n⚠️ Errors: {errors}")
