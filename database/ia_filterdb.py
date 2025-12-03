# database/ia_filterdb.py (Updated to fix ImportError)
import re
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.file_id import FileId 
from config import Config 

# MongoDB Connection
client = AsyncIOMotorClient(Config.DB_URI)
db = client["IndexingBotDB"]
files_collection = db["files"]       # Main collection for indexed files
settings_collection = db["settings"] # Collection for skip ID

# --- Helper Functions (Pyrogram File ID Handling) ---
def get_file_details(media):
    """Media object se file_reference aur file_type nikalna."""
    
    # Check if media object is valid and has a file_id
    if not hasattr(media, 'file_id') or not media.file_id:
        return None, "unknown"

    try:
        file_id_obj = FileId.decode(media.file_id)
        file_ref = file_id_obj.file_reference
    except Exception:
        # Agar decode fail ho, toh file_ref ko None set karein
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

# --- 1. File Saving Function ---
async def save_file(media, caption):
    """Saves a file's details into the database, handles reference and cleaning."""
    file_id = media.file_id
    file_unique_id = media.file_unique_id
    
    # File ID Handling: file_ref aur file_type nikalna
    file_ref, file_type = get_file_details(media)
    
    file_name = media.file_name if media.file_name else f"file_{file_unique_id}"
    file_size = media.file_size

    # --- Naam Saaf Karna (Clean) ---
    cleaned_name = re.sub(r"(_|\-|\.|\+)", " ", file_name).strip().lower()
    
    # Check for duplicate using file_unique_id (unique index assume karte hue)
    duplicate_check = await files_collection.find_one({"file_unique_id": file_unique_id})
    if duplicate_check:
        return 'duplicate'

    # Prepare data based on Media Schema
    data = {
        "file_id": file_id, 
        "file_ref": file_ref, # Permanent File Reference (bytes format)
        "file_unique_id": file_unique_id, # Duplicate check ke liye
        "file_name": file_name, 
        "file_size": file_size,
        "file_type": file_type, 
        "caption": caption, 
        "cleaned_name": cleaned_name, 
    }
    
    try:
        await files_collection.insert_one(data)
        return 'success'
    except Exception as e:
        if "DuplicateKeyError" in str(e): 
             return 'duplicate'
        print(f"Error saving file: {e}")
        return 'error'

# --- 2. Skip ID Functions ---
async def get_current_skip_id():
    setting = await settings_collection.find_one({"_id": "skip_id"})
    # client.DEFAULT_SKIP_ID config se aayega
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
    
    search_fields = [{"cleaned_name": regex_pattern}]
    
    # Check if caption filter is configured and should be included in search
    if getattr(Config, 'USE_CAPTION_FILTER', False):
         search_fields.append({"caption": regex_pattern})
         
    query_filter["$or"] = search_fields

    # Optional: File Type Filter
    if file_type:
        query_filter["file_type"] = file_type

    cursor = files_collection.find(query_filter).skip(offset).limit(max_results)
    results = await cursor.to_list(length=max_results)
    
    return results
