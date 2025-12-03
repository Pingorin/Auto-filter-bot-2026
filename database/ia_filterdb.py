# database/ia_filterdb.py (Updated with Schema and Search Logic)

import re
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.file_id import FileId, FileType, unpack_new_file_id
from config import Config

# MongoDB Connection (Assuming client, db are already initialized)
client = AsyncIOMotorClient(Config.DB_URI)
db = client["IndexingBotDB"]
files_collection = db["files"] 
settings_collection = db["settings"]

# --- 1. Database Index Setup (Important for Fast Search) ---
async def setup_db_indexes():
    """Ensures file_name and file_unique_id have indexes."""
    try:
        # 1. file_name index for fast searching (Text Indexing)
        await files_collection.create_index(
            [("file_name", "text")], 
            name="file_name_search_index"
        )
        
        # 2. file_unique_id index to prevent duplicates
        await files_collection.create_index(
            "file_unique_id", 
            unique=True, 
            name="file_unique_id_index"
        )
        print("MongoDB indexes created successfully.")
    except Exception as e:
        print(f"Error creating MongoDB indexes: {e}")

# Call setup_db_indexes() during bot startup in bot.py!

# --- Helper Function (Technical) ---
def get_file_details(media):
    """Unpacks Pyrogram's file ID and extracts details."""
    if not media:
        return None, None, None, None
        
    # Pyrogram's unpack_new_file_id breaks down file_id into permanent parts
    file_id_parts = unpack_new_file_id(media.file_id)
    
    # file_ref (bytes) is crucial for persistent storage
    file_ref = file_id_parts.file_reference
    
    return {
        "file_id": media.file_id,                     # Original ID (less important for resend)
        "file_unique_id": media.file_unique_id,       # Unique ID (important for duplicate check)
        "file_ref": file_ref,                         # Permanent File Reference (important for resend)
        "file_name": media.file_name,
        "file_size": media.file_size,
        "file_type": media.media.value,               # 'video', 'document', 'audio'
        "caption": media.caption or ""                # Caption ko empty string rakha hai agar missing ho
    }

# --- 2. save_file Function (Asli Saving) ---
async def save_file(media):
    details = get_file_details(media)
    if not details:
        return 'error'

    # Clean Name Logic: Replace common separators with space for better search
    clean_name = re.sub(r"(_|\-|\.|\+)", " ", details['file_name']).lower()
    details['clean_name'] = clean_name # Nayi field for efficient search (optional)

    # 1. Duplicate Check & Commit
    try:
        # Insert with file_unique_id index applied
        await files_collection.insert_one(details)
        return 'success'

    except Exception as e:
        if 'E11000 duplicate key' in str(e): # MongoDB DuplicateKeyError code
            return 'duplicate'
        else:
            print(f"Database insertion error: {e}")
            return 'error'

# --- 3. get_search_results Function (Searching) ---
async def get_search_results(query: str, file_type: str = None, max_results: int = 10, offset: int = 0):
    
    # Regex Banana (User query ko search-friendly banana)
    # Yeh pattern "query" ko "query", "q.u.e.r.y", "query-" jaise sabhi forms se match karega.
    query_regex = re.escape(query).replace(" ", ".*?")
    
    # Base Query Filter
    filter_query = {
        "file_name": {"$regex": query_regex, "$options": "i"} # Case-insensitive search
    }

    # File Type Filter
    if file_type:
        filter_query["file_type"] = file_type
        
    # --- Optional: Caption Filtering Logic (Agar Config mein enable ho) ---
    # Agar aap caption me bhi dhoondna chahte hain, to yeh logic use karein
    # if Config.USE_CAPTION_FILTER: # Assume this is a config variable
    #     filter_query = {
    #         "$or": [
    #             {"file_name": {"$regex": query_regex, "$options": "i"}},
    #             {"caption": {"$regex": query_regex, "$options": "i"}}
    #         ]
    #     }
    # Agar aapne Text Index use kiya hai to $text: search use karna behtar hai.
    
    cursor = files_collection.find(filter_query).sort("_id", 1).skip(offset).limit(max_results)
    
    results = await cursor.to_list(length=max_results)
    total_count = await files_collection.count_documents(filter_query)
    
    return results, total_count
