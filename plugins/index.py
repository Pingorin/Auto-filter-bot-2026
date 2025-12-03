# plugins/index.py
import asyncio
import re
import time
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.ia_filterdb import save_file, get_current_skip_id, set_new_skip_id

# --- Global State and Locks ---
INDEX_LOCK = asyncio.Lock()
# Current status tracking (kise index kiya jaa raha hai)
temp = {
    "CURRENT": 0,    # Message ID jahan se shuru karna hai (Skip ID)
    "CANCEL": False  # Agar indexing cancel karni hai
}

# --- 1. Indexing Request Dena (send_for_index) ---
@Client.on_message(filters.private & (filters.regex(r'^https?://t\.me/[^/]+/\d+') | filters.forwarded))
async def send_for_index(client: Client, message: Message):
    """
    Handles indexing initiation via forwarded message or link.
    """
    if message.from_user.id not in client.ADMINS:
        # Indexing sirf Admin hi shuru kar sakte hain
        return await message.reply_text("🚫 **Access Denied.** Only bot admins can initiate the indexing process.")

    if not message.text and not message.forward_from_chat:
        return # Skip if not link or forward

    # --- Extract Channel ID and Message ID ---
    chat_id = None
    last_msg_id = None
    
    if message.forward_from_chat:
        # Forwarded message
        chat_id = message.forward_from_chat.id
        last_msg_id = message.forward_from_message_id
    elif message.text:
        # Link
        match = re.search(r't\.me/([^/]+)/(\d+)', message.text)
        if match:
            try:
                # Username ya public link se ID nikalna
                chat = await client.get_chat(match.group(1))
                chat_id = chat.id
                last_msg_id = int(match.group(2))
            except Exception as e:
                return await message.reply_text(f"🚫 Error: Could not resolve channel/chat link. {e}")
        else:
            return await message.reply_text("🚫 Invalid Telegram link format.")
            
    if not chat_id:
        return await message.reply_text("🚫 Could not determine Channel ID.")
        
    # --- Check Bot's Status in Channel ---
    try:
        # Check if the bot is a member of the channel
        await client.get_chat_member(chat_id, 'me')
    except Exception:
        return await message.reply_text("🚫 **Bot is not a member** of this channel. Please add the bot first.")

    # --- Request Message Creation ---
    request_text = (
        f"**📣 Indexing Request**\n\n"
        f"Channel ID: `{chat_id}`\n"
        f"Last Message ID (Target): `{last_msg_id}`\n"
        f"Requested By: {message.from_user.mention} (`{message.from_user.id}`)"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Accept Index", f"index#{chat_id}#{last_msg_id}"),
            InlineKeyboardButton("❌ Reject Index", f"reject#{chat_id}")
        ]
    ])

    # --- Admin Request (DM mein seedhe button) ---
    await message.reply_text(
        f"**Index Request Accepted (Admin)**. Proceed to start indexing?",
        reply_markup=buttons
    )
    # Note: Normal user request yahan se hata diya gaya hai, kyunki /index command Admin-only hai.


# --- 2. Request Approve Karna (index_files) ---
@Client.on_callback_query(filters.regex(r'^index#'))
async def index_files(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in client.ADMINS:
        return await callback_query.answer("You are not authorized to approve indexing.", show_alert=True)
        
    if INDEX_LOCK.locked():
        return await callback_query.answer("Indexing is already running. Please wait.", show_alert=True)
        
    await INDEX_LOCK.acquire()
    temp["CANCEL"] = False 
    
    try:
        _, chat_id_str, last_msg_id_str = callback_query.data.split('#')
        chat_id = int(chat_id_str)
        last_msg_id = int(last_msg_id_str)
    except:
        await INDEX_LOCK.release()
        return await callback_query.answer("Invalid request data.", show_alert=True)
        
    await callback_query.answer("Starting Indexing Process...", show_alert=True)
    
    status_msg = await callback_query.message.edit_text(
        "⏳ **Starting Indexing...** Please wait.\n\n"
        f"Channel: `{chat_id}`\nLast ID: `{last_msg_id}`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel Indexing", "cancel")]])
    )
    
    await index_files_to_db(client, chat_id, last_msg_id, status_msg)

# --- 2.1 Cancel Indexing ---
@Client.on_callback_query(filters.regex('^cancel'))
async def cancel_indexing_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in client.ADMINS:
        return await callback_query.answer("You are not authorized to cancel.", show_alert=True)

    if not INDEX_LOCK.locked():
        return await callback_query.answer("No indexing process is running.", show_alert=True)
        
    temp["CANCEL"] = True
    await callback_query.answer("Cancellation request sent...", show_alert=True)

# --- 2.2 Reject Indexing ---
@Client.on_callback_query(filters.regex(r'^reject#'))
async def reject_indexing(client: Client, callback_query: CallbackQuery):
    """Handles the rejection of an indexing request."""
    if callback_query.from_user.id not in client.ADMINS:
        return await callback_query.answer("You are not authorized to reject indexing.", show_alert=True)
        
    try:
        _, chat_id_str = callback_query.data.split('#')
        chat_id = int(chat_id_str)
    except:
        return await callback_query.answer("Invalid request data.", show_alert=True)

    await callback_query.message.edit_text(
        f"❌ **Indexing Request Rejected**\n\nChannel ID: `{chat_id}`\nRejected by: {callback_query.from_user.mention}"
    )
    await callback_query.answer("Indexing request rejected.", show_alert=True)


# --- 3. Asli Indexing (index_files_to_db) ---
async def index_files_to_db(client: Client, chat_id: int, last_msg_id: int, status_msg: Message):
    
    total_files = 0
    duplicate_files = 0
    messages_fetched = 0
    no_media_count = 0
    deleted_count = 0
    unsupported_count = 0
    error_count = 0
    start_time = time.time()
    
    temp["CURRENT"] = await get_current_skip_id()
    
    try:
        # last_msg_id ko limit ke roop mein istemal karna
        async for message in client.iter_messages(chat_id, limit=last_msg_id, offset=temp["CURRENT"]):
            
            messages_fetched += 1
            
            if temp["CANCEL"]:
                await status_msg.edit_text("❌ Indexing Cancelled by Admin.")
                break
                
            if message.empty:
                deleted_count += 1
                continue
                
            if not message.media:
                no_media_count += 1
                continue
                
            # --- Media Type Check ---
            if message.video or message.audio or message.document:
                media = message.video or message.audio or message.document
                file_caption = message.caption if message.caption else ""
                
                status = await save_file(media, file_caption)
                
                if status == 'success':
                    total_files += 1
                elif status == 'duplicate':
                    duplicate_files += 1
                elif status == 'error':
                    error_count += 1
                
            else:
                unsupported_count += 1
                
            # --- Status Update (Har 60 messages ke baad) ---
            if messages_fetched % 60 == 0:
                elapsed_time = time.time() - start_time
                status_text = (
                    "**⏳ Indexing Progress...**\n\n"
                    f"Messages Scanned: **{messages_fetched}**\n"
                    f"Saved Files: **{total_files}**\n"
                    f"Duplicates Found: **{duplicate_files}**\n"
                    f"Errors: **{error_count}**\n"
                    f"Skipped/Unsupported: {deleted_count} deleted, {no_media_count} no media, {unsupported_count} unsupported.\n"
                    f"Time Elapsed: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}\n"
                    f"Current Msg ID: **{message.id}**"
                )
                await set_new_skip_id(message.id)
                
                try:
                    await status_msg.edit_text(status_text, reply_markup=status_msg.reply_markup)
                except Exception:
                    pass

    except Exception as e:
        final_text = f"🚨 Indexing Failed:\n`{e}`"
    else:
        final_text = "**✅ Indexing Complete!**"

    # --- Poora Hone Par Cleanup ---
    elapsed_time = time.time() - start_time
    summary = (
        f"\n\n--- **Final Summary** ---\n"
        f"Total Messages Scanned: **{messages_fetched}**\n"
        f"Files Successfully Indexed: **{total_files}**\n"
        f"Duplicates/Already Indexed: **{duplicate_files}**\n"
        f"Total Errors: **{error_count}**\n"
        f"Time Taken: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}"
    )
    
    await status_msg.edit_text(final_text + summary, reply_markup=None)
    
    if INDEX_LOCK.locked():
        INDEX_LOCK.release()
        
    temp["CURRENT"] = 0
