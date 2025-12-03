import logging
import asyncio
import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UsernameNotOccupied, PeerIdInvalid, RPCError

# Import Database function
from database.ia_filter import save_file # Media class ki zaroorat nahi hai yahan
import config

logger = logging.getLogger(__name__)

# --- Temporary State Management ---
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
        # Pyrogram mein media ke type ke naam par attribute hota hai (e.g., message.video)
        return getattr(message, message.media.value)
    return None

# --- Link Parsing and Indexing Start ---

@Client.on_message(filters.private & filters.command("index") & filters.user(config.ADMINS))
async def index_start(bot, message):
    if len(message.command) < 2:
        await message.reply("Usage: `/index https://t.me/channel_link or /index @username`")
        return
    
    link_or_username = message.command[1]
    
    # 1. Link Parsing (Robust Logic)
    try:
        if "t.me/" in link_or_username:
            # t.me/c/1234567/10 ya t.me/username/10
            link = link_or_username.split("/")
            chat_id_part = link[-2]

            if chat_id_part.isdigit():
                # Private channel link: /c/1234567. chat_id = -1001234567
                target_chat_id = int(f"-100{chat_id_part}")
            else:
                # Public channel/username: @username
                target_chat_id = link_or_username
        elif link_or_username.startswith('@'):
            target_chat_id = link_or_username
        else:
            await message.reply("Invalid link or username format.")
            return

        # Chat ID Verify karna
        chat = await bot.get_chat(target_chat_id)
        target_chat_id = chat.id # Final numeric chat_id use karein

    except (UsernameNotOccupied, PeerIdInvalid):
        await message.reply("Error: Channel/User not found or Invalid ID.")
        return
    except RPCError as e:
        await message.reply(f"Telegram RPC Error: {e.MESSAGE}")
        return
    except Exception as e:
        await message.reply(f"An unexpected error occurred during link parsing: {e}")
        return

    # 2. Indexing Function Call
    await index_files_to_db(bot, message.chat.id, target_chat_id, message)

# --- Actual Indexing Loop ---

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
        
        # Channel ka title nikalna
        try:
            chat_title = (await bot.get_chat(target_chat_id)).title
        except:
            chat_title = target_chat_id
        
        status_msg = await bot.send_message(
            admin_chat_id,
            f"⏳ **Initializing Indexing for {chat_title}...**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel", callback_data="index_cancel")]])
        )

        try:
            # Iterating History
            # Pyrogram ka iter_messages ya get_chat_history dono use kar sakte hain
            async for msg in bot.get_chat_history(target_chat_id):
                if Temp.CANCEL:
                    break

                Temp.CURRENT += 1
                
                # Check Media
                media = get_media_from_message(msg)
                if not media:
                    continue

                # 3. Direct Save (MediaObject class ki zaroorat nahi)
                # Hum save_file function ko seedhe Pyrogram media object bhejte hain, 
                # aur save_file() ia_filter.py mein iske attributes ko handle karega.
                
                # save_file function (jo ia_filter.py mein hai) ko Pyrogram media object bhejna
                status, _ = await save_file(media, msg.caption, msg.chat.id, msg.id)
                
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
                            f"🔄 **Indexing: {chat_title}**\n"
                            f"Scanned: {Temp.CURRENT}\n"
                            f"Saved: {total_files}\n"
                            f"Duplicate: {duplicate}",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel", callback_data="index_cancel")]])
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                    except:
                        pass # Small errors ignore karna

        except Exception as e:
            await bot.send_message(admin_chat_id, f"Error in Indexing: {e}")
            logger.error(f"Indexing Error: {e}")

        # Final Summary
        await status_msg.edit(
            f"✅ **Indexing Completed for {chat_title}**\n"
            f"Total Scanned: {Temp.CURRENT}\n"
            f"Saved: {total_files}\n"
            f"Duplicate: {duplicate}\n"
            f"Errors: {errors}"
        )

# --- Cancel Handler ---

@Client.on_callback_query(filters.regex("index_cancel") & filters.user(config.ADMINS))
async def cancel_handler(bot, query):
    Temp.CANCEL = True
    await query.answer("Cancelling...", show_alert=True)
