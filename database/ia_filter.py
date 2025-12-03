import logging
import re
import config
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient
from umongo import Document, fields
import sys

# Logger Setup
logger = logging.getLogger(__name__)

# ######################################################
# ### UNIVERSAL UMONGO/MOTOR INSTANCE IMPORT LOGIC ###
# ######################################################
try:
    # 1. Sabse common naya path (umongo v4.x)
    from umongo.frameworks.motor import MotorAsyncIOInstance
except ImportError:
    try:
        # 2. Purana/Alternative path (umongo v3.x)
        from umongo.frameworks import MotorAsyncIOInstance
    except ImportError:
        # 3. Agar koi bhi kaam na kare, toh toh dependency issue hai.
        logger.critical(
            "CRITICAL: Failed to import MotorAsyncIOInstance from umongo. "
            "Bot will not run without proper database connectivity. "
            "Please check umongo and motor versions in requirements.txt."
        )
        sys.exit(1)

# --- MongoDB Connection ---
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DATABASE_NAME]

# 2. Sahi Initialization
try:
    # Ab yeh MotorAsyncIOInstance class se initialize hoga
    instance = MotorAsyncIOInstance(db) 
    logger.info("MongoDB Instance successfully initialized.")
except TypeError as e:
    logger.error(f"UMONGO INIT FATAL ERROR: {e}. Check if umongo is compatible with motor version.")
    sys.exit(1) 
# ######################################################


# --- 1. Database Structure (Schema) ---
@instance.register
class Media(Document):
    # FIX: 'file_id' ko '_id' se map karne wala error dene wala syntax hata diya
    # Umongo ko aamtaur par field ka naam '_id' hi dena behtar hota hai agar primary key use karni hai.
    # Lekin yahan hum is field ko 'file_unique_id' kehte hain aur 'save_file' mein '_id' set karte hain.
    file_unique_id = fields.StrField(required=True) # <-- Naya naam
    
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
        # Text Indexing for Fast Search
        indexes = ('$file_name', )

# --- 2. Save File Function (Asli Saving & Cleaning) ---
async def save_file(media):
    """File ko database mein save karta hai (Unpack ID -> Clean Name -> Commit)"""
    file_id = media.file_id # Telegram se aaya hua file_id

    try:
        # Check if file already exists using file_id (jo '_id' mein save hoga)
        file = await Media.find_one({'_id': file_id})
        if file:
            return 'duplicate', 0

        # --- Data Cleaning and Preparation ---
        file_ref = getattr(media, "file_ref", None)
        original_name = getattr(media, "file_name", "")
        
        if not original_name and media.caption:
            original_name = media.caption.splitlines()[0]
        
        # Naam Saaf Karna (Cleaning using Regex: _, -, ., + ko space se badalna)
        clean_name = re.sub(r"(_|\-|\.|\+)", " ", original_name)
        clean_name = clean_name.strip()

        # Media Object creation and commit
        media_file = Media(
            # '_id' field ko Telegram ke file_id se set karna (Duplicate check yahi se hota hai)
            _id=file_id, 
            file_unique_id=file_id, # Schema mein bhi save karna (optional)
            
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
# ... (Search function ko waisa hi rakhenge, usmein koi syntax error nahi hai)
async def get_search_results(query, max_results=10, offset=0, lang_code=None):
    """User ki query se files search karta hai."""
    query = query.strip()
    if not query:
        return []

    # Regex banana (Case Insensitive Search)
    regex = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)

    # Database Filter Query (Caption filtering optional)
    if config.USE_CAPTION_FILTER: # Yeh variable config.py mein hona chahiye
        filter_criteria = {
            '$or': [
                {'file_name': regex},
                {'caption': regex}
            ]
        }
    else:
        filter_criteria = {'file_name': regex}

    # Database se find karna (skip aur limit ke saath)
    cursor = Media.find(filter_criteria)
    cursor.sort('$natural', -1) # Naye files pehle dikhenge
    cursor.skip(offset).limit(max_results)

    files = await cursor.to_list(length=max_results)
    return files
