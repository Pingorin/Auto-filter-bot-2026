import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from database.ia_filterdb import Media
from info import ADMINS

@Client.on_message(filters.command("index") & filters.user(ADMINS))
async def index_channel(bot, message):
    
    if len(message.command) < 2:
        return await message.reply("Channel ID dijiye!\nExample: `/index -100123456789`")
    
    try:
        chat_id = int(message.command[1])
    except:
        return await message.reply("❌ Invalid Channel ID format!")

    msg = await message.reply("🧐 Connecting to Channel...")
    
    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await msg.edit(f"❌ Error: Main channel access nahi kar pa raha.\nReason: `{e}`")

    await msg.edit(f"✅ Connected: **{chat.title}**\n📂 Scanning for files... (Yeh naya tareeka hai)")
    
    total_files = 0
    duplicate = 0
    errors = 0

    # Hum 2 baar scan karenge. Pehle Videos, fir Documents.
    # Isse wo 'BOT_METHOD_INVALID' error nahi aayega.
    
    filter_types = [enums.MessagesFilter.VIDEO, enums.MessagesFilter.DOCUMENT]
    
    for filter_type in filter_types:
        try:
            # Note: search_messages Bot ke liye allowed hai
            async for message in bot.search_messages(chat_id, filter=filter_type):
                media = message.video or message.document
                
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

                # Update Status every 20 files
                if total_files % 20 == 0:
                    await msg.edit(f"Indexing {chat.title}...\n\nSaved: {total_files}\nDuplicates: {duplicate}")
                    
        except Exception as e:
            print(f"Loop Error: {e}")
            # Agar koi error aaye to agle loop par chale jao
            continue

    await msg.edit(f"✅ **Indexing Complete!**\n\n📂 Total Saved: {total_files}\n♻️ Duplicates: {duplicate}\n⚠️ Errors: {errors}")
