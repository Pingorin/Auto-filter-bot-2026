# database/ia_filterdb.py (Reverted to Umongo 2.x compatible syntax)
import re
from motor.motor_asyncio import AsyncIOMotorClient
# umongo 2.x ke liye set_motor_backend zaroori hai aur root se import hota hai
from umongo import Document, fields, set_motor_backend 
from umongo.frameworks import MotorAsyncIOInstance
from pyrogram.file_id import FileId 
from config import Config 

# --- MongoDB and umongo Setup ---
# MongoDB Connection
client = AsyncIOMotorClient(Config.DB_URI)
db = client["IndexingBotDB"]
# umongo instance ko motor/asyncIO backend se initialize karna
instance = MotorAsyncIOInstance(db)

# FIX: Umongo 2.x mein yeh call zaroori hai
set_motor_backend(instance)

# --- Document Schema Definition using umongo ---

@instance.register
class Media(Document):
    """
    Database mein save hone wali har media file ka schema.
    """
    # 1. Primary Fields
    file_id = fields.StrField(required=True)
    file_unique_id = fields.StrField(required=True, unique=True) # Duplicate check ke liye
    file_ref = fields.BinaryField(required=True) # Permanent File Reference (bytes format)
    
    # 2. Metadata Fields
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(required=True) # 'video', 'audio', 'document'
    
    # FIX: default="" parameter wapas laaya gaya hai (Umongo 2.x ke liye sahi)
    caption = fields.StrField(default="") 
    
    # 3. Search Index Field
    cleaned_name = fields.StrField(required=True)
    
    class Meta:
        indexes = ('cleaned_name',)
        collection_name = "files"

# settings collection (Skip ID tracking)
settings_collection = db["settings"] 

# --- Helper Function: Pyrogram File ID Handling ---
def get_file_details(media):
    """Media object se file_reference aur file_type nikalna."""
    
    if not hasattr(media, 'file_id') or not media.file_id:
        return None, "unknown"

    try:
        file_id_obj = FileId.decode(media.file_id)
        # file_ref bytes format mein milega
        file_ref = file_id_obj.file_reference
    except Exception:
        file_ref = None
    
    # File Type nikalna
    if hasattr(media, 'video') and media.video:
        file_type = "video"
    elif hasattr(media, 'audio') and media.audio:
        file_type = "audio"
    elif hasattr(media, 'document') and media.document:
        file_type = "document"
    else:
        file_type = "unknown"
        
    return file_ref, file_type

# --- 1. File Saving Function (Using umongo Document) ---
async def save_file(media, caption):
    """Saves a file's details into the database using the umongo Media schema."""
    file_id = media.file_id
    file_unique_id = media.file_unique_id
    
    file_ref, file_type = get_file_details(media)
    
    file_name = media.file_name if media.file_name else f"file_{file_unique_id}"
    file_size = media.file_size

    # --- Naam Saaf Karna (Clean) ---
    cleaned_name = re.sub(r"(_|\-|\.|\+)", " ", file_name).strip().lower()
    
    # umongo Document banana
    file_doc = Media(
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_ref=file_ref,
        file_name=file_name,
        file_size=file_size,
        file_type=file_type,
        caption=caption,
        cleaned_name=cleaned_name,
    )

    try:
        # Document ko save karna
        await file_doc.commit()
        return 'success'
    except Exception as e:
        if "DuplicateKeyError" in str(e): 
             return 'duplicate'
        print(f"Error saving file: {e}")
        return 'error'

# --- 2. Skip ID Functions (Using raw motor for simplicity) ---
async def get_current_skip_id():
    setting = await settings_collection.find_one({"_id": "skip_id"})
    return setting.get("value", Config.DEFAULT_SKIP_ID) if setting else Config.DEFAULT_SKIP_ID

async def set_new_skip_id(new_id):
    await settings_collection.update_one(
        {"_id": "skip_id"},
        {"$set": {"value": new_id}},
        upsert=True
    )

# --- 3. get_search_results Function (Searching) ---
async def get_search_results(query: str, file_type: str = None, max_results: int = 10, offset: int = 0):
    """Searches the database using Regex."""
    
    search_query = re.sub(r"(_|\-|\.|\+)", " ", query).strip().lower()
    
    query_filter = {}
    
    # Regex pattern: Case-Insensitive search
    regex_pattern = re.compile(f".*{re.escape(search_query)}.*", re.IGNORECASE)
    
    # Cleaned_name field par search karna
    search_fields = [{"cleaned_name": regex_pattern}]
    
    if getattr(Config, 'USE_CAPTION_FILTER', False):
         search_fields.append({"caption": regex_pattern})
         
    query_filter["$or"] = search_fields

    # Optional: File Type Filter
    if file_type:
        query_filter["file_type"] = file_type

    # umongo Document class use karke find karna
    cursor = Media.find(query_filter).skip(offset).limit(max_results)
    
    results = await cursor.to_list(length=max_results)
    
    return results
