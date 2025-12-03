import logging
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
import config

# Database Connection
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DATABASE_NAME] # Config me DATABASE_NAME add kar lena
instance = Instance(db)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    chat_id = fields.IntField(allow_none=True)
    message_id = fields.IntField(allow_none=True)

    class Meta:
        collection_name = "media_files"

async def save_file(media):
    """
    File ko database mein save karta hai.
    Returns: 'success', 'duplicate', ya 'error'
    """
    try:
        file_id = media.file_id
        file_ref = media.file_ref
        file_name = media.file_name
        file_size = media.file_size
        file_type = media.file_type
        mime_type = media.mime_type
        caption = media.caption
        chat_id = media.chat_id
        message_id = media.message_id
        
        # Check if file already exists
        file = await Media.find_one({'file_id': file_id})
        if file:
            return 'duplicate'

        # Create new entry
        new_file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            caption=caption,
            chat_id=chat_id,
            message_id=message_id
        )
        
        await new_file.commit()
        return 'success'

    except DuplicateKeyError:
        return 'duplicate'
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        return 'error'
