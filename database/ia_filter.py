import logging
import re
import config
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient
from umongo import Document, fields
import sys

# Logger Setup...

# UMONGO/MOTOR INSTANCE IMPORT LOGIC (pichla fix)
try:
    from umongo.frameworks.motor import MotorAsyncIOInstance
except ImportError:
    try:
        from umongo.frameworks import MotorAsyncIOInstance
    except ImportError:
        logger.critical("CRITICAL: Failed to import MotorAsyncIOInstance from umongo.")
        sys.exit(1)

# --- MongoDB Connection ---
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DATABASE_NAME]

# Sahi Initialization
try:
    instance = MotorAsyncIOInstance(db) 
    logger.info("MongoDB Instance successfully initialized.")
except TypeError as e:
    logger.error(f"UMONGO INIT FATAL ERROR: {e}")
    sys.exit(1) 
# ######################################################


# --- 1. Database Structure (Schema) ---
@instance.register
class Media(Document):
    # FIX: '_id' ko primary key bana diya. Ispe 'required=True' theek kaam karta hai.
    _id = fields.StrField(required=True) 
    
    # file_unique_id ko required=True se hataya taaki AttributeError na aaye
    file_unique_id = fields.StrField() 
    
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True) # Isko filhal rakhte hain
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    chat_id = fields.IntField(allow_none=True)
    message_id = fields.IntField(allow_none=True)

    class Meta:
        collection_name = "media_files"
        indexes = ('$file_name', )


# --- 2. Save File Function (Asli Saving & Cleaning) ---
async def save_file(media):
    """File ko database mein save karta hai"""
    file_id = media.file_id # Telegram se aaya hua file_id

    try:
        # Check if file already exists using _id (jo file_id hai)
        file = await Media.find_one({'_id': file_id})
        if file:
            return 'duplicate', 0

        # --- Data Cleaning and Preparation ---
        # ... (cleaning logic remains same)
        file_ref = getattr(media, "file_ref", None)
        original_name = getattr(media, "file_name", "")
        if not original_name and media.caption:
            original_name = media.caption.splitlines()[0]
        clean_name = re.sub(r"(_|\-|\.|\+)", " ", original_name).strip()

        # Media Object creation and commit
        media_file = Media(
            _id=file_id, 
            file_unique_id=file_id, 
            file_ref=file_ref,
            file_name=clean_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption,
            chat_id=getattr(media, "chat_id", None),
            message_id=getattr(media, "message_id", None)
        )

        await media_file.commit()
        return 'success', 0

    except DuplicateKeyError:
        logger.warning(f"Duplicate File: {getattr(media, 'file_name', 'Unknown')}")
        return 'duplicate', 0
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return 'error', e

# --- 3. Search Function (Indexing & Regex) ---
# ... (Remains the same)
async def get_search_results(query, max_results=10, offset=0, lang_code=None):
    """User ki query se files search karta hai."""
    query = query.strip()
    if not query:
        return []

    regex = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)

    if config.USE_CAPTION_FILTER: 
        filter_criteria = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter_criteria = {'file_name': regex}

    cursor = Media.find(filter_criteria)
    cursor.sort('$natural', -1)
    cursor.skip(offset).limit(max_results)

    files = await cursor.to_list(length=max_results)
    return files
