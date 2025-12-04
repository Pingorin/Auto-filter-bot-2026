import asyncio
from pyrogram import Client
from pyrogram.types import Message
from typing import Dict, Any, Optional
import time

# आवश्यक क्लास और फ़ंक्शंस आयात करें
from database.ia_filterdb import Media, save_file_in_db

# --- Global State for Indexing ---
INDEXING_STATUS: Dict[int, bool] = {} 

def get_media_details(message: Message, chat_id: int) -> Optional[Media]:
    """
    Pyrogram Message ऑब्जेक्ट से Media dataclass के लिए आवश्यक विवरण निकालता है।
    """
    
    file_type = message.document or message.video or message.audio
    if not file_type:
        return None

    # Note: Telegram में file_ref bytes ऑब्जेक्ट है, इसे DB में bytes के रूप में स्टोर करें
    file_id = file_type.file_id
    file_ref = file_type.file_ref
    file_name = getattr(file_type, "file_name", "Unknown File")
    file_size = file_type.file_size
    mime_type = file_type.mime_type
    caption = message.caption or ""
    
    # Unique ID: chat_id और message_id का संयोजन
    unique_id = f"{chat_id}_{message.id}" 

    return Media(
        _id=unique_id,
        file_id=file_id,
        file_ref=file_ref.to_bytes(), 
        file_name=file_name,
        file_size=file_size,
        caption=caption,
        f_storage_path=str(chat_id),
        mime_type=mime_type,
        quality=None, # यहाँ से quality/year एक्सट्रैक्ट करने का लॉजिक जोड़ा जा सकता है
        year=None,    # यहाँ से quality/year एक्सट्रैक्ट करने का लॉजिक जोड़ा जा सकता है
        date=message.date,
        is_deleted=False
    )

async def start_channel_scan(client: Client, chat_id: int, admin_id: int, progress_message: Message):
    """
    चैनल के इतिहास को स्कैन करता है और फ़ाइलों को डेटाबेस में इंडेक्स करता है।
    """
    
    global INDEXING_STATUS
    INDEXING_STATUS[chat_id] = True
    
    indexed_count = 0
    skipped_count = 0
    
    try:
        chat = await client.get_chat(chat_id)
        chat_title = chat.title
        await client.edit_message_text(
            chat_id=progress_message.chat.id,
            message_id=progress_message.id,
            text=f"⏳ **इंडेक्सिंग शुरू:** `{chat_title}` ({chat_id})\n\n"
        )
        
        async for message in client.get_chat_history(chat_id):
            
            if not INDEXING_STATUS.get(chat_id, False):
                await client.edit_message_text(
                    chat_id=progress_message.chat.id,
                    message_id=progress_message.id,
                    text=f"⚠️ **इंडेक्सिंग रुकावट:** `{chat_title}` ({chat_id}) पर इंडेक्सिंग रोक दी गई है।"
                )
                break
            
            media_obj = get_media_details(message, chat_id)
            
            if media_obj:
                await save_file_in_db(media_obj)
                indexed_count += 1
            else:
                skipped_count += 1
            
            # हर 50 फ़ाइलों के बाद प्रगति अपडेट करें
            if (indexed_count + skipped_count) % 50 == 0 and indexed_count > 0:
                await client.edit_message_text(
                    chat_id=progress_message.chat.id,
                    message_id=progress_message.id,
                    text=f"🔄 **इंडेक्सिंग प्रगति:** `{chat_title}`\n\n"
                         f"✅ इंडेक्स किए गए: `{indexed_count}`\n"
                         f"⏭️ छोड़े गए: `{skipped_count}`"
                )
            
            await asyncio.sleep(0.5) # थ्रॉटलिंग से बचने के लिए

        # --- Indexing Complete ---
        if INDEXING_STATUS.get(chat_id, False):
            await client.edit_message_text(
                chat_id=progress_message.chat.id,
                message_id=progress_message.id,
                text=f"🎉 **इंडेक्सिंग पूरी हुई:** `{chat_title}`\n\n"
                     f"कुल फ़ाइलें इंडेक्स की गईं: `{indexed_count}`"
            )

    except Exception as e:
        error_msg = f"❌ **इंडेक्सिंग त्रुटि:** `{chat_title}`\n\n" \
                    f"त्रुटि: {type(e).__name__}: {str(e)}"
        
        await client.edit_message_text(
            chat_id=progress_message.chat.id,
            message_id=progress_message.id,
            text=error_msg
        )
        
    finally:
        INDEXING_STATUS.pop(chat_id, None)

def stop_channel_scan(chat_id: int) -> bool:
    """चैनल के लिए चल रहे स्कैन को रोकता है।"""
    global INDEXING_STATUS
    if chat_id in INDEXING_STATUS:
        INDEXING_STATUS[chat_id] = False
        return True
    return False
