from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from main import filter_col # MongoDB कलेक्शन को मुख्य फ़ाइल से इंपोर्ट करें
import logging
import time

logger = logging.getLogger(__name__)

# इंडेक्सिंग के दौरान क्रैश से बचने के लिए एक साधारण लॉक
is_indexing = False 

# --- इंडेक्स कमांड हैंडलर ---
@Client.on_message(filters.command("index") & filters.private)
async def index_handler(client: Client, message: Message):
    global is_indexing
    
    # 1. एडमिन चेक
    if message.from_user.id not in Config.ADMINS:
        await message.reply_text("❌ आपको यह कमांड चलाने की अनुमति नहीं है। यह केवल एडमिन के लिए है।")
        return

    # 2. चैनल चेक
    if not Config.CHANNELS:
        await message.reply_text("❌ `Config.CHANNELS` में कोई चैनल ID नहीं मिला। कृपया अपनी Heroku Config Vars में `CHANNELS` वेरिएबल सेट करें।")
        return

    # 3. इंडेक्सिंग लॉक चेक
    if is_indexing:
        await message.reply_text("⏳ इंडेक्सिंग पहले से ही चल रही है। कृपया समाप्त होने का इंतज़ार करें।")
        return
    
    is_indexing = True
    total_indexed_files = 0
    start_time = time.time()
    
    await message.reply_text("🔍 **इंडेक्सिंग शुरू हो रही है...**\n\nचैनल से फ़ाइलों को MongoDB में सेव किया जा रहा है। इसमें समय लग सकता है।")

    try:
        # प्रत्येक चैनल में फ़ाइलों को इंडेक्स करें
        for channel_id in Config.CHANNELS:
            current_indexed = 0
            offset = 0
            
            # Channel ID को @username के रूप में या नेगेटिव ID के रूप में हैंडल करें
            channel_name = channel_id if isinstance(channel_id, str) else str(channel_id)

            await client.send_message(message.chat.id, f"**▶️ चैनल से फ़ाइलें पढ़ना शुरू करें:** `{channel_name}`")

            while True:
                # 100 मैसेज का बैच खींचें
                history = await client.get_history(channel_id, offset=offset, limit=100)
                if not history.messages:
                    break # जब कोई और मैसेज न हो तो लूप तोड़ दें

                records = []
                for msg in history.messages:
                    if msg.media and (msg.video or msg.document or msg.audio):
                        # फ़ाइल का डेटा निकालें
                        file = msg.video or msg.document or msg.audio
                        
                        record = {
                            'file_id': file.file_id,
                            'file_ref': file.file_ref, # फ़ाइल को बाद में भेजने के लिए ज़रूरी
                            'file_name': file.file_name.lower() if file.file_name else None,
                            'message_id': msg.id,
                            'chat_id': msg.chat.id,
                            'file_size': file.file_size,
                            'caption': msg.caption.lower() if msg.caption else None,
                        }
                        if record['file_name']:
                            records.append(record)
                
                # यदि रिकॉर्ड्स हैं, तो उन्हें MongoDB में एक साथ डालें
                if records:
                    await filter_col.insert_many(records)
                    current_indexed += len(records)

                # हर 1000 फ़ाइलों पर अपडेट दें
                if current_indexed % 1000 == 0 and current_indexed > 0:
                    await client.send_message(message.chat.id, 
                        f"🔄 `{channel_name}` में `{current_indexed}` फ़ाइलें इंडेक्स की गईं...")
                
                offset += 100 # अगले 100 मैसेज पर जाएँ
            
            total_indexed_files += current_indexed
            await client.send_message(message.chat.id, 
                f"✅ **चैनल इंडेक्सिंग पूर्ण:** `{channel_name}`\nकुल फ़ाइलें: `{current_indexed}`")
            
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        await message.reply_text(f"❌ इंडेक्सिंग त्रुटि आई: `{e}`")
        
    finally:
        is_indexing = False
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)
        
        await message.reply_text(f"🎉 **सभी इंडेक्सिंग पूर्ण!**\n\nकुल इंडेक्स की गई फ़ाइलें: **{total_indexed_files}**\nसमय लगा: **{elapsed_time}** सेकंड्स")

