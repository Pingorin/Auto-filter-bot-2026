import logging
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

# Import Database function
from database.ia_filter import save_file, Media
import config

logger = logging.getLogger(__name__)

class Temp:
    CANCEL = False
    CURRENT = 0
    LOCK = asyncio.Lock()

# --- Helper to Extract Media ---
def get_media_from_message(message):
    media_types = [
        enums.MessageMediaType.VIDEO,
        enums.MessageMediaType.AUDIO,
        enums.MessageMediaType.DOCUMENT
    ]
    if message.media in media_types:
        return getattr(message, message.media.value)
    return None

# --- Indexing Logic ---

@Client.on_message(filters.private & filters.command("index") & filters.user(config.ADMINS))
async def index_start(bot, message):
    if len(message.command) < 2:
        await message.reply("Usage: `/index https://t.me/channel_link`")
        return
    
    link = message.command[1]
    # Link parsing logic (Simple example for t.me/xxx/123)
    # Asli bot me regex se chat_id nikalna behtar hota hai
    try:
        if "t.me/" in link:
            parts = link.split("/")
            if parts[-2].isdigit(): # Private/Public handling logic needed here
                 chat_id = int(f"-100{parts[-2]}") # This is rough logic
            else:
                 chat_username = parts[-2]
                 chat = await bot.get_chat(chat_username)
                 chat_id = chat.id
    except Exception as e:
        await message.reply(f"Invalid Link: {e}")
        return

    await index_files_to_db(bot, message.chat.id, chat_id, message)

async def index_files_to_db(bot, admin_chat_id, target_chat_id, command_msg):
    if Temp.LOCK.locked():
        await bot.send_message(admin_chat_id, "⚠️ Already indexing another channel. Please wait.")
        return

    async with Temp.LOCK:
        Temp.CANCEL = False
        Temp.CURRENT = 0
        total_files = 0
        duplicate = 0
        errors = 0
        
        status_msg = await bot.send_message(
            admin_chat_id,
            "⏳ **Initializing Indexing...**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel", callback_data="index_cancel")]])
        )

        try:
            # Iterating History
            async for msg in bot.get_chat_history(target_chat_id):
                if Temp.CANCEL:
                    break

                Temp.CURRENT += 1
                
                # Check Media
                media = get_media_from_message(msg)
                if not media:
                    continue

                # Prepare Custom Object for save_file
                # Hum wahi object structure bhej rahe hain jo ia_filter expect karta hai
                class MediaObject:
                    file_id = media.file_id
                    file_ref = getattr(media, "file_ref", None)
                    file_name = getattr(media, "file_name", "")
                    file_size = media.file_size
                    file_type = media.mime_type if hasattr(media, 'mime_type') else "unknown"
                    mime_type = getattr(media, "mime_type", "None")
                    caption = msg.caption
                    
                    # Agar naam nahi hai (e.g. video without filename attribute)
                    if not file_name:
                         file_name = f"File_{media.file_unique_id}"

                # Call Save Function
                status, _ = await save_file(MediaObject())
                
                if status == 'success':
                    total_files += 1
                elif status == 'duplicate':
                    duplicate += 1
                elif status == 'error':
                    errors += 1

                # Update Status every 100 messages
                if Temp.CURRENT % 100 == 0:
                    try:
                        await status_msg.edit(
                            f"🔄 **Indexing...**\n"
                            f"Scanned: {Temp.CURRENT}\n"
                            f"Saved: {total_files}\n"
                            f"Duplicate: {duplicate}",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel", callback_data="index_cancel")]])
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                    except:
                        pass

        except Exception as e:
            await bot.send_message(admin_chat_id, f"Error: {e}")

        await status_msg.edit(
            f"✅ **Indexing Completed**\n"
            f"Total Scanned: {Temp.CURRENT}\n"
            f"Saved: {total_files}\n"
            f"Duplicate: {duplicate}\n"
            f"Errors: {errors}"
        )

@Client.on_callback_query(filters.regex("index_cancel") & filters.user(config.ADMINS))
async def cancel_handler(bot, query):
    Temp.CANCEL = True
    await query.answer("Cancelling...", show_alert=True)
