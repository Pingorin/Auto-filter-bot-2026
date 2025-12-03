import logging
import re
import config
from pymongo.errors import DuplicateKeyError
# Nayi Import Line: umongo.frameworks.Motor use karein
from umongo.frameworks import Motor 
from umongo import Document, fields
from motor.motor_asyncio import AsyncIOMotorClient

# Logger Setup
logger = logging.getLogger(__name__)

# --- MongoDB Connection ---
# MongoDB Connection (Client, Database)
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DATABASE_NAME]

# Sahi Tareeka: umongo.frameworks.Motor se initialize karein
instance = Motor(db) 
# ---------------------------

# --- 1. Database Structure (Schema) ---
@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id') # Unique ID (Primary Key)
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
        # Text Indexing for Fast Search ($file_name)
        indexes = ('$file_name', )

# --- 2. Save File Function (Asli Saving & Cleaning) ---
async def save_file(media):
    """
    File ko database mein save karta hai.
    Process: Unpack ID -> Clean Name -> Commit -> Handle Duplicate
    """
    try:
        # 1. Details Extract karna
        file_id = media.file_id
        file_ref = getattr(media, "file_ref", None)
        original_name = getattr(media, "file_name", "")
        file_size = media.file_size
        file_type = media.file_type
        mime_type = getattr(media, "mime_type", "None")
        caption = getattr(media, "caption", None)

        # Agar file name nahi hai, toh caption se naam banane ki koshish karein
        if not original_name and caption:
            original_name = caption.splitlines()[0]

        # 2. Naam Saaf Karna (Cleaning using Regex)
        # _ - . + ko hata kar space lagana
        clean_name = re.sub(r"(_|\-|\.|\+)", " ", original_name)
        clean_name = clean_name.strip() # Aage peeche ki spaces hatana

        # 3. Create Media Object
        media_file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=clean_name, # Clean kiya hua naam save hoga
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            caption=caption,
            chat_id=getattr(media, "chat_id", None), # Added default safe access
            message_id=getattr(media, "message_id", None) # Added default safe access
        )

        # 4. Database mein Commit karna
        await media_file.commit()
        return 'success', 0 # Success

    except DuplicateKeyError:
        # Agar file pehle se hai
        logger.warning(f"Duplicate File: {getattr(media, 'file_name', 'Unknown')}")
        return 'duplicate', 0
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return 'error', e

# --- 3. Search Function (Indexing & Regex) ---
async def get_search_results(query, max_results=10, offset=0, lang_code=None):
    """
    User ki query se files search karta hai.
    """
    query = query.strip()
    
    # Check for empty query
    if not query:
        return []

    # Regex banana (Case Insensitive Search)
    # User ne "matrix" likha to "The Matrix", "Matrix Reloaded" sab match hoga
    # re.escape se special characters sahi handle honge
    regex = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)

    # Database Filter Query
    if config.USE_CAPTION_FILTER: # Config se check karein
        filter_criteria = {
            '$or': [
                # MongoDB Text Indexing ($file_name) is usually faster for full text search
                # But PyMongo uses standard Regex filters if not using the $text operator explicitly.
                # Regex Filter:
                {'file_name': regex},
                {'caption': regex}
            ]
        }
    else:
        filter_criteria = {'file_name': regex}

    # Database se find karna (skip aur limit ke saath)
    cursor = Media.find(filter_criteria)
    
    # Sort by ID (newest first) aur Pagination
    cursor.sort('$natural', -1)
    cursor.skip(offset).limit(max_results)

    files = await cursor.to_list(length=max_results)
    return files
