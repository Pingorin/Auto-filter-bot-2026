import logging
import asyncio
import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

# Import Database functions
from database.ia_filter import save_file
import config

# Logger setup
logger = logging.getLogger(__name__)

# Temporary Data Storage (Locks & Cancel Flags)
class Temp:
    CANCEL = False
    CURRENT = 0
    LOCK = asyncio.Lock()
    START_TIME = 0

# --- Helper Functions ---

def get_media_details(message):
    """Message se media object nikalta hai"""
    media = message.media
    if media == enums.MessageMediaType.DOCUMENT:
        return message.document
    elif media == enums.MessageMediaType.VIDEO:
        return message.video
    elif media == enums.MessageMediaType.AUDIO:
        return message.audio
    return None

# --- Step 1: User Request for Indexing ---

@Client.on_message(filters.private & filters.command("index"))
async def send_for_index(bot, message):
    if message.from_user.id not in config.ADMINS:
        # Agar normal user hai to request Log Channel me bhejo
        await bot.send_message(
            chat_id=config.LOG_CHANNEL,
            text=f"**📝 New Index Request**\n\n**User:** {message.from_user.mention}\n**ID:** `{message.from_user.id}`\n**Request:** {message.text}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Accept", callback_data=f"index_accept#{message.from_user.id}")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"index_reject#{message.from_user.id}")]
            ])
        )
        await message.reply("Your request has been sent to Admins for approval.")
        return

    # Agar Admin hai to seedha process shuru karo (Simplified for Admin)
    await message.reply("Admin detected. Use /batch command directly or reply to a channel link.")

# --- Step 2: Admin Approval (Callback) ---

@Client.on_callback_query(filters.regex(r'^index_accept'))
async def index_files(bot, query):
    if query.from_user.id not in config.ADMINS:
        await query.answer("You are not authorized!", show_alert=True)
        return

    # Check if lock is active
    if Temp.LOCK.locked():
        await query.answer("Wait! Another indexing process is running.", show_alert=True)
        return

    # Extract user_id from callback data
    user_id = int(query.data.split("#")[1])
    
    # Request accept notification
    await query.message.edit_text(f"Indexing Request Accepted by {query.from_user.mention}.\nStarting Indexing...")
    try:
        await bot.send_message(user_id, "✅ Your indexing request has been accepted! Starting now...")
    except:
        pass

    # Start the heavy lifting
    await index_files_to_db(bot, query.message)

@Client.on_callback_query(filters.regex(r'^index_cancel'))
async def cancel_index(bot, query):
    if query.from_user.id not in config.ADMINS:
        return
    Temp.CANCEL = True
    await query.answer("Stopping Indexing...", show_alert=True)

# --- Step 3: Real Indexing Logic ---

async def index_files_to_db(bot, message):
    # Lock lagana
    async with Temp.LOCK:
        Temp.CANCEL = False
        Temp.CURRENT = 0 # Skip value (iska logic aap /setskip command se jod sakte ho)
        
        # Example: Link se chat_id nikalna (Yahan aapko message se link parse karna hoga)
        # Assuming message text contains the chat ID or link logic handle karna hoga
        # Simplification ke liye maan lete hain hum LOG_CHANNEL me jo msg aaya tha usme target chat ka info tha
        
        # NOTE: Is example ke liye main target_chat_id hardcode ya context se le raha hu.
        # Asli code me aapko `query.message.reply_to_message` se channel ID nikalni padegi.
        
        total_files = 0
        duplicate = 0
        errors = 0
        deleted = 0
        no_media = 0
        unsupported = 0
        
        msg = await message.reply_text(
            "⏳ **Indexing Started...**\n\nFetched: 0\nSaved: 0\nDuplicate: 0",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel", callback_data="index_cancel")]])
        )

        # Pyrogram ka iter_history use karenge (efficient way)
        # Note: Aapko target_chat_id define karna padega jahan se file uthani hai
        target_chat_id = -1001234567890 # Example ID, replace logic with dynamic ID
        
        try:
            async for msg_obj in bot.get_chat_history(target_chat_id):
                
                # 1. Cancel Check
                if Temp.CANCEL:
                    await msg.edit(f"❌ Indexing Cancelled!\n\nSaved: {total_files}\nDuplicate: {duplicate}")
                    return

                Temp.CURRENT += 1

                # 2. Deleted/Empty Check
                if msg_obj.empty:
                    deleted += 1
                    continue

                # 3. Media Check
                media_file = get_media_details(msg_obj)
                if not media_file:
                    no_media += 1
                    continue

                # 4. Save to Database
                # Pyrogram object ko hamare DB format me convert karna
                file_info = Media(
                    file_id=media_file.file_id,
                    file_ref=getattr(media_file, "file_ref", None), # Old pyrogram versions support
                    file_name=getattr(media_file, "file_name", "Unknown"),
                    file_size=media_file.file_size,
                    file_type=msg_obj.media.value,
                    mime_type=getattr(media_file, "mime_type", "None"),
                    caption=msg_obj.caption,
                    chat_id=msg_obj.chat.id,
                    message_id=msg_obj.id
                )

                result = await save_file(file_info)
                
                if result == 'success':
                    total_files += 1
                elif result == 'duplicate':
                    duplicate += 1
                else:
                    errors += 1

                # 5. Status Update (Every 60 messages)
                if Temp.CURRENT % 60 == 0:
                    try:
                        await msg.edit(
                            f"🔄 **Indexing in Progress**\n\n"
                            f"Total Fetched: {Temp.CURRENT}\n"
                            f"Saved: {total_files}\n"
                            f"Duplicate: {duplicate}\n"
                            f"Errors: {errors}",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel", callback_data="index_cancel")]])
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                    except Exception:
                        pass

        except Exception as e:
            logging.error(f"Error in indexing loop: {e}")
            await msg.edit(f"⚠️ Error Occurred: {e}")
        
        # Final Summary
        await msg.edit(
            f"✅ **Indexing Completed!**\n\n"
            f"Total Messages Scanned: {Temp.CURRENT}\n"
            f"Saved: {total_files}\n"
            f"Duplicates: {duplicate}\n"
            f"No Media: {no_media}\n"
            f"Deleted: {deleted}"
        )
