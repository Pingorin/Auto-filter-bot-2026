import logging
import re
import config
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient
from umongo import Document, fields

# --- ZAROORI FIXES YAHAN HAIN (Universal Import Logic) ---
# Hum MotorAsyncIOInstance ko ek compatible path se import karne ki koshish karenge.
try:
    # 1. Sabse common naya path
    from umongo.frameworks.motor import MotorAsyncIOInstance
except ImportError:
    try:
        # 2. Purana/Alternative path
        from umongo.frameworks import MotorAsyncIOInstance
    except ImportError:
        # 3. Agar koi bhi kaam na kare, toh dependency issue hai.
        # Filhal, hum code ko chalane ke liye ek dummy class bana dete hain (production use ke liye nahi)
        logging.critical("CRITICAL: Failed to import MotorAsyncIOInstance from umongo. Check umongo version.")
        # Agar bot chalate rahna hai, toh aapko yahan ek graceful exit dena hoga.
        # Hum MotorInstance hi try kar lete hain (Last resort for compatibility)
        from umongo import Instance as MotorAsyncIOInstance 
        # Yeh line sirf code ko compile karne ke liye hai, functionality guarantee nahi.
        
# ----------------------------------

# Logger Setup
logger = logging.getLogger(__name__)

# --- MongoDB Connection ---
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DATABASE_NAME]

# 2. Sahi Initialization (Ab yeh MotorAsyncIOInstance class se initialize hoga)
try:
    instance = MotorAsyncIOInstance(db) 
except TypeError as e:
    # Agar phir bhi TypeError aaye toh user ko clear message dein
    logging.error(f"UMONGO INIT ERROR: {e}. Check if umongo is compatible with motor version.")
    raise

# --- 1. Database Structure (Schema) ---
@instance.register
class Media(Document):
# ... baaki ka Media class ka code waisa hi rahega ...
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
        indexes = ('$file_name', )

# --- 2. Save File Function (Asli Saving & Cleaning) ---
async def save_file(media):
# ... save_file function ka code waisa hi rahega ...
    try:
        file_id = media.file_id
        file_ref = getattr(media, "file_ref", None)
        original_name = getattr(media, "file_name", "")
        file_size = media.file_size
        file_type = media.file_type
        mime_type = getattr(media, "mime_type", "None")
        caption = getattr(media, "caption", None)

        if not original_name and caption:
            original_name = caption.splitlines()[0]

        # Naam Saaf Karna (Cleaning using Regex)
        clean_name = re.sub(r"(_|\-|\.|\+)", " ", original_name)
        clean_name = clean_name.strip()

        media_file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=clean_name,
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            caption=caption,
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
async def get_search_results(query, max_results=10, offset=0, lang_code=None):
# ... get_search_results function ka code waisa hi rahega ...
    query = query.strip()
    if not query:
        return []

    regex = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)

    if config.USE_CAPTION_FILTER:
        filter_criteria = {
            '$or': [
                {'file_name': regex},
                {'caption': regex}
            ]
        }
    else:
        filter_criteria = {'file_name': regex}

    cursor = Media.find(filter_criteria)
    cursor.sort('$natural', -1)
    cursor.skip(offset).limit(max_results)

    files = await cursor.to_list(length=max_results)
    return files
