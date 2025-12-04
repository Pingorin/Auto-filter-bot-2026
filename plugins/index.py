from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

# लोकल फ़ाइलें आयात करें
from config import Config
from plugins.channel import start_channel_scan, stop_channel_scan, INDEXING_STATUS
from database.ia_filterdb import delete_file_from_db

# --- Helper Function: Admin Check ---
def is_admin(user_id: int) -> bool:
    """जांच करता है कि क्या user ID Config में दिए गए ADMINS लिस्ट में है।"""
    return user_id in Config.ADMINS 


# --- 1. /index Command Handler ---
@Client.on_message(filters.command("index") & filters.private)
async def index_channel_handler(client: Client, message: Message):
    """एडमिन द्वारा इंडेक्सिंग प्रक्रिया शुरू करने के लिए कमांड।"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ यह कमांड केवल मेरे एडमिन के लिए है।")
        return

    if len(message.command) < 2:
        await message.reply_text("❓ उपयोग: `/index <channel_username_or_id>`")
        return

    target_chat = message.command[1].strip()
    try:
        chat = await client.get_chat(target_chat)
        chat_id = chat.id
    except Exception:
        await message.reply_text("❌ अमान्य चैनल ID/Username, या मैं उस चैनल में एडमिन नहीं हूँ।")
        return

    if chat_id in INDEXING_STATUS and INDEXING_STATUS[chat_id]:
        await message.reply_text(f"⚠️ `{chat.title}` ({chat_id}) पहले से ही इंडेक्स किया जा रहा है।")
        return

    progress_message = await message.reply_text(
        f"✅ इंडेक्सिंग शुरू हो रही है... `{chat.title}`"
    )
    
    asyncio.create_task(
        start_channel_scan(client, chat_id, user_id, progress_message)
    )


# --- 2. /stopindex Command Handler ---
@Client.on_message(filters.command("stopindex") & filters.private)
async def stop_index_handler(client: Client, message: Message):
    """चल रही इंडेक्सिंग प्रक्रिया को रोकने के लिए कमांड।"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ यह कमांड केवल मेरे एडमिन के लिए है।")
        return

    if len(message.command) < 2:
        await message.reply_text("❓ उपयोग: `/stopindex <channel_id>`")
        return
        
    try:
        target_chat = message.command[1].strip()
        chat = await client.get_chat(target_chat)
        chat_id = chat.id
    except Exception:
        await message.reply_text("❌ अमान्य चैनल ID/Username।")
        return

    if stop_channel_scan(chat_id):
        await message.reply_text(f"🛑 `{chat.title}` ({chat_id}) के लिए इंडेक्सिंग को रोकने का अनुरोध किया गया।")
    else:
        await message.reply_text(f"ℹ️ `{chat.title}` ({chat_id}) के लिए कोई सक्रिय इंडेक्सिंग नहीं मिल रही है।")


# --- 3. /unindex Command Handler (Soft Delete Logic) ---
@Client.on_message(filters.command("unindex") & filters.private)
async def unindex_handler(client: Client, message: Message):
    """फ़ाइल ID के आधार पर एक फ़ाइल को डेटाबेस से सॉफ्ट डिलीट करता है।"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ यह कमांड केवल मेरे एडमिन के लिए है।")
        return

    if len(message.command) < 2:
        await message.reply_text("❓ उपयोग: `/unindex <file_id>` (फ़ाइल ID `chat_id_message_id` फॉर्मेट में होती है।)")
        return
        
    file_id_to_delete = message.command[1].strip()
    
    success = await delete_file_from_db(file_id_to_delete)
    
    if success is True:
        await message.reply_text(f"🗑️ फ़ाइल ID `{file_id_to_delete}` सफलतापूर्वक **सॉफ्ट डिलीट** कर दी गई है।")
    elif success is False:
        await message.reply_text(f"❌ फ़ाइल ID `{file_id_to_delete}` डेटाबेस में नहीं मिली।")
    else:
        await message.reply_text("🚨 डेटाबेस त्रुटि: फ़ाइल को डिलीट करने में समस्या आई।")
