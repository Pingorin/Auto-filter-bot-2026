import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.ia_filterdb import Media
from info import ADMINS

# Temporary Storage for Steps (RAM me data rakhega)
INDEX_CACHE = {}

# --- STEP 1: Command Aaya ---
@Client.on_message(filters.command("index") & filters.user(ADMINS))
async def step_one_index(bot, message):
    # User ko cache me daal do ki wo abhi indexing process me hai
    INDEX_CACHE[message.from_user.id] = {
        'state': 'waiting_forward',
        'chat_id': None,
        'last_msg_id': 0,
        'skip': 0
    }
    await message.reply_text(
        "**🆔 Step 1:**\n\nApne Movie Channel se **Last Message** (sabse niche wala) yahan **Forward** karo.\n\nIsse mujhe pata chalega ki kahan tak scan karna hai."
    )

# --- STEP 2: Forward Message Aaya ---
@Client.on_message(filters.forward & filters.user(ADMINS))
async def step_two_forward(bot, message):
    user_id = message.from_user.id
    
    # Check agar user ne /index command diya tha
    if user_id in INDEX_CACHE and INDEX_CACHE[user_id]['state'] == 'waiting_forward':
        
        # Data extract karo
        try:
            target_chat_id = message.forward_from_chat.id
            last_msg_id = message.forward_from_message_id
        except:
            return await message.reply("❌ Sahi se forward nahi hua. Channel se direct forward karein.")

        # Cache update
        INDEX_CACHE[user_id]['chat_id'] = target_chat_id
        INDEX_CACHE[user_id]['last_msg_id'] = last_msg_id
        INDEX_CACHE[user_id]['state'] = 'waiting_skip'

        await message.reply_text(
            f"✅ Channel Detected: `{target_chat_id}`\n📄 Last Message ID: `{last_msg_id}`\n\n**🆔 Step 2:**\nAb **Skip Number** bhejo.\n(Agar shuru se scan karna hai to `0` bhejo)."
        )

# --- STEP 3: Number (Skip) Aaya ---
@Client.on_message(filters.text & filters.user(ADMINS))
async def step_three_skip(bot, message):
    user_id = message.from_user.id
    
    # Check state
    if user_id in INDEX_CACHE and INDEX_CACHE[user_id]['state'] == 'waiting_skip':
        try:
            skip = int(message.text)
        except:
            return await message.reply("❌ Kripya sirf number bhejein (Example: 0).")

        # Data save
        INDEX_CACHE[user_id]['skip'] = skip
        INDEX_CACHE[user_id]['state'] = 'ready'
        
        data = INDEX_CACHE[user_id]
        total_approx = data['last_msg_id'] - skip

        # Buttons Dikhana
        buttons = [[
            InlineKeyboardButton(f"🚀 Start Indexing ({total_approx} Files)", callback_data="start_index"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_index")
        ]]
        
        await message.reply_text(
            f"📊 **Indexing Summary**\n\n"
            f"📢 Channel ID: `{data['chat_id']}`\n"
            f"🔢 Total Messages to Scan: `{total_approx}`\n"
            f"⏭ Skip First: `{skip}` messages\n\n"
            f"Kya main start karu?",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# --- STEP 4: Start Button Click Hua ---
@Client.on_callback_query(filters.regex("^start_index"))
async def start_indexing_callback(bot, query):
    user_id = query.from_user.id
    
    if user_id not in INDEX_CACHE or INDEX_CACHE[user_id]['state'] != 'ready':
        return await query.answer("Session expired. Dobara /index karein.", show_alert=True)

    data = INDEX_CACHE[user_id]
    chat_id = data['chat_id']
    last_id = data['last_msg_id']
    skip = data['skip']
    
    # Cache clear kar do
    del INDEX_CACHE[user_id]
    
    await query.message.edit_text("⏳ **Initializing...** Connection check kar raha hu...")
    
    # Indexing Logic Starts
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    
    # Status Message
    status_msg = query.message
    
    # Loop Logic (Batch Processing for Speed)
    # Hum 200-200 messages ka batch uthayenge
    current_id = skip + 1
    
    try:
        while current_id <= last_id:
            # Batch calculate karo
            end_id = min(current_id + 200, last_id + 1)
            ids_to_fetch = list(range(current_id, end_id))
            
            try:
                # Get Messages (Ye 'Blind Bot' issue solve karta hai)
                messages = await bot.get_messages(chat_id, ids_to_fetch)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                continue
            except Exception as e:
                await status_msg.edit(f"❌ Critical Error: `{e}`")
                return

            for message in messages:
                # Agar message deleted hai (None)
                if message is None or message.empty:
                    deleted += 1
                    continue
                
                # Media Check
                media = message.document or message.video or message.audio
                if media:
                    # Database Save Call
                    res = await Media.save_file(media)
                    if res == 'saved':
                        total_files += 1
                    elif res == 'duplicate':
                        duplicate += 1
                    elif res == 'error':
                        errors += 1
                else:
                    # Text message wagera
                    deleted += 1

            # Har 200 messages ke baad status update
            try:
                await status_msg.edit(
                    f"⚙️ **Indexing in Progress...**\n\n"
                    f"📥 Fetched: {current_id} / {last_id}\n"
                    f"✅ Saved: {total_files}\n"
                    f"♻️ Duplicates: {duplicate}\n"
                    f"🗑️ Skipped/Deleted: {deleted}\n"
                    f"⚠️ Errors: {errors}"
                )
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                pass
            
            # Next Batch
            current_id += 200

    except Exception as e:
        await status_msg.reply(f"❌ Indexing Stopped due to error: {e}")

    await status_msg.edit(
        f"✅ **Indexing Completed Successfully!**\n\n"
        f"📂 Total Saved: **{total_files}**\n"
        f"♻️ Duplicates Skipped: **{duplicate}**\n"
        f"🗑️ Other Messages: **{deleted}**\n"
        f"⚠️ Errors: **{errors}**"
    )

# --- Cancel Button ---
@Client.on_callback_query(filters.regex("^cancel_index"))
async def cancel_indexing(bot, query):
    if query.from_user.id in INDEX_CACHE:
        del INDEX_CACHE[query.from_user.id]
    await query.message.edit("❌ Indexing Cancelled.")
