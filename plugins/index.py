from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from main import filter_col, user_client # user_client को इंपोर्ट करें
import logging
import time

logger = logging.getLogger(__name__)

# इंडेक्सिंग के दौरान क्रैश से बचने के लिए एक साधारण लॉक
is_indexing = False 

# --- 1. /index कमांड हैंडलर ---
@Client.on_message(filters.command("index") & filters.private)
async def index_start_request_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS:
        return
    if is_indexing:
        await message.reply_text("⏳ इंडेक्सिंग पहले से ही चल रही है।")
        return
    if not user_client:
         await message.reply_text("❌ यूज़र क्लाइंट शुरू नहीं हो सका। कृपया `USER_SESSION` Config Var को जांचें और सुनिश्चित करें कि बॉट एडमिन है।")
         return
    if not Config.CHANNELS:
        await message.reply_text("❌ `CHANNELS` Config Var सेट नहीं है।")
        return
        
    await message.reply_text(
        "**फ़ाइल फॉरवर्ड करें!**\n\nकृपया जिस चैनल को इंडेक्स करना है, उस चैनल से **सबसे पुरानी** या **कोई भी एक फ़ाइल** यहाँ फॉरवर्ड करें।\n\n_(यह आपके चैनल ID की पुष्टि करेगा।)_"
    )

# --- 2. Forwaded File Handler (Indexing Logic) ---
@Client.on_message(filters.forwarded & (filters.document | filters.video | filters.audio) & filters.private)
async def index_file_forward_handler(client: Client, message: Message):
    global is_indexing
    
    if message.from_user.id not in Config.ADMINS:
        return

    # 1. जाँच करें कि फ़ाइल फॉरवर्ड की गई है
    if not message.forward_from_chat:
        await message.reply_text("❌ यह एक फॉरवर्ड की गई फ़ाइल नहीं है। कृपया चैनल से फ़ाइल को फॉरवर्ड करें।")
        return

    channel_id = message.forward_from_chat.id
    
    # 2. Config Vars में चैनल ID की जाँच करें
    if channel_id not in Config.CHANNELS:
        await message.reply_text(f"❌ चैनल `{channel_id}` आपकी Config Vars की `CHANNELS` लिस्ट में नहीं है।")
        return

    if is_indexing:
        await message.reply_text("⏳ इंडेक्सिंग पहले से ही चल रही है।")
        return

    is_indexing = True
    total_indexed_files = 0
    start_time = time.time()
    
    await message.reply_text(
        f"🔍 **इंडेक्सिंग शुरू हो रही है...**\nचैनल `{channel_id}` से फ़ाइलें MongoDB में सेव की जा रही हैं। यह कुछ समय लेगा।"
    )

    try:
        # यहाँ हम यूज़र क्लाइंट का उपयोग करते हैं
        offset = 0
        while True:
            # यूज़र क्लाइंट (user_client) का उपयोग करें!
            history = await user_client.get_history(channel_id, offset=offset, limit=100)
            if not history.messages:
                break 

            records = []
            for msg in history.messages:
                # केवल फ़ाइलें जो वीडियो, डॉक्यूमेंट या ऑडियो हैं
                if msg.media and (msg.video or msg.document or msg.audio):
                    file = msg.video or msg.document or msg.audio
                    
                    record = {
                        # फ़ाइल को भेजने के लिए file_id और file_ref आवश्यक हैं
                        'file_id': file.file_id, 
                        'file_ref': file.file_ref, 
                        'file_name': file.file_name.lower() if file.file_name else None,
                        'message_id': msg.id,
                        'chat_id': msg.chat.id,
                        'file_size': file.file_size,
                        'caption': msg.caption.lower() if msg.caption else None,
                    }
                    if record['file_name']:
                        records.append(record)
            
            if records:
                # Duplicates से बचने के लिए इसे ठीक से संभालना चाहिए, 
                # लेकिन अभी हम सीधे insert_many कर रहे हैं।
                await filter_col.insert_many(records)
                total_indexed_files += len(records)
            
            offset += 100
            
            if total_indexed_files % 1000 == 0 and total_indexed_files > 0:
                await client.send_message(message.chat.id, 
                    f"🔄 `{channel_id}` में `{total_indexed_files}` फ़ाइलें इंडेक्स की गईं...")
        
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        await message.reply_text(f"❌ इंडेक्सिंग त्रुटि आई: `{e}`")
        
    finally:
        is_indexing = False
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)
        
        await message.reply_text(f"🎉 **सभी इंडेक्सिंग पूर्ण!**\nकुल इंडेक्स की गई फ़ाइलें: **{total_indexed_files}**\nसमय लगा: **{elapsed_time}** सेकंड्स")
