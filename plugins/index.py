import asyncio
from pyrogram import Client, filters
from database.ia_filterdb import Media
from info import ADMINS

# Sirf ADMINS ye command use kar sakte hain
@Client.on_message(filters.command("index") & filters.user(ADMINS))
async def index_channel(bot, message):
    
    # Command check: /index -100123456789
    if len(message.command) < 2:
        return await message.reply("Channel ID do! Example: `/index -100xxxxxx`")
    
    try:
        chat_id = int(message.command[1])
    except:
        return await message.reply("Invalid Channel ID!")

    msg = await message.reply("Processing... Files dhoondh raha hu 🧐")
    
    total_files = 0
    duplicate = 0
    errors = 0

    # History Loop (Channel ke purane messages padhna)
    async for message in bot.get_chat_history(chat_id):
        media = None
        
        # Check agar Document ya Video hai
        if message.document:
            media = message.document
        elif message.video:
            media = message.video
            
        if media:
            try:
                # File save karo
                saved = await Media.save_file(media)
                if saved:
                    total_files += 1
                else:
                    duplicate += 1
                    
                # Har 20 files ke baad update do
                if total_files % 20 == 0:
                    await msg.edit(f"Indexing...\nSaved: {total_files}\nDuplicates: {duplicate}")
                    
            except Exception as e:
                errors += 1
                print(f"Error: {e}")

    await msg.edit(f"✅ Indexing Complete!\n\n📂 Total Saved: {total_files}\n♻️ Duplicates: {duplicate}\n⚠️ Errors: {errors}")
