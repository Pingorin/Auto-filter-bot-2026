import datetime
import re
from umongo import Document, fields
from umongo.frameworks.motor import MotorCollection
from info import Config
from pyrogram.types import Message

# File Media Document Model
@Config.db_instance.register
class Media(Document):
    # Collection name 'filter_files'
    collection = MotorCollection(Config.DATABASE_NAME, "filter_files") 
    
    # File ke unique fields
    file_id = fields.StrField(required=True) # Telegram file_id
    file_ref = fields.StrField(default=None) # Telegram file_ref (optional, fast access ke liye)
    file_name = fields.StrField(required=True) # Filename
    file_size = fields.IntField(required=True) # Size in bytes
    file_type = fields.StrField(required=True) # 'video', 'document', 'audio' etc.
    mime_type = fields.StrField(required=True) # MIME type

    # File ka source/location
    channel_id = fields.IntField(required=True) # Channel ID jahan file store hai
    message_id = fields.IntField(required=True) # Message ID jahan file store hai

    # File jodi gayi thi
    date = fields.DateTimeField(default=lambda: datetime.datetime.utcnow())

    # Indexes: Search aur uniqueness ke liye
    class Meta:
        # file_name par index, case-insensitive search ke liye
        indexes = [("file_name", {"collation": {"locale": "en", "strength": 2}})]
        # file_id aur channel_id ko unique rakhein
        # unique_together = (("file_id", "channel_id",)) # agar ek channel mein duplicate allowed nahi

### 2. Save Function Structure

async def save_file(media_message: Message):
    """Telegram Message object se file details ko database mein store karein."""
    # Media object extract karein (video, document, ya audio)
    media = media_message.video or media_message.document or media_message.audio
    
    if not media:
        return # Agar koi media nahi hai toh return karein

    # Media document banayein
    media_doc = Media(
        file_id=media.file_id,
        file_ref=media.file_ref.encode('base64', 'url').decode('utf-8') if media.file_ref else None,
        file_name=getattr(media, "file_name", "Unknown"),
        file_size=getattr(media, "file_size", 0),
        file_type=media_message.media.value, # 'video', 'document', etc.
        mime_type=getattr(media, "mime_type", "application/octet-stream"),
        channel_id=media_message.chat.id,
        message_id=media_message.id,
    )

    try:
        await media_doc.commit()
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

### 3. Search Function Structure

async def get_search_results(query: str, offset: int = 0, limit: int = 10):
    """
    MongoDB mein files ko Regular Expressions (Regex) ka istemaal karke search karein.
    """
    # Case-insensitive search ke liye query ko escape karein aur regex banayein
    # 're.IGNORECASE' aur 'collation' dono ka istemaal behtar hai
    regex = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)

    # Search query
    search_query = {
        "file_name": regex # File name mein regex match karein
    }

    # Files ko search karein, sort karein, skip karein aur limit karein
    cursor = Media.find(search_query).sort("file_name").skip(offset).limit(limit)

    # Search results ko list mein load karein
    search_results = await cursor.to_list(length=limit)
    
    # Total count (pagination ke liye)
    total_count = await Media.count_documents(search_query)

    return search_results, total_count
