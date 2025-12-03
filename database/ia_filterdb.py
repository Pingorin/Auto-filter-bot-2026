# database/ia_filterdb.py

import re
from motor.motor_asyncio import AsyncIOMotorClient
# Note: Pyrogram 2.0+ mein file_id modules mein hai
from pyrogram.file_id import FileId, FileType, unpack_file_id, pack_file_id 
from config import Config

# --- MongoDB Connection ---
client = AsyncIOMotorClient(Config.DB_URI)
db = client["IndexingBotDB"]
files_collection = db["files"] 
settings_collection = db["settings"] # Skip ID saving ke liye

# --- 1. Database Index Setup (Important for Fast Search) ---
async def setup_db_indexes():
    """Ensures file_name and file_unique_id have indexes."""
    try:
        # 1. file_name index for fast searching (Text Indexing)
        # Agar aap advanced search chahte hain, toh 'text' index banayein:
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
        # Index creation sirf ek baar hona chahiye. Agar index pehle se ho to yeh error aayega.
        if "Index with name" not in str(e) and "file_name_search_index" not in str(e):
             print(f"Error creating MongoDB indexes: {e}")

# --- Helper Function (Technical) ---
def get_file_details(media):
    """Unpacks Pyrogram's file ID and extracts details."""
    if not media:
        return None
        
    # Pyrogram 2.0+ mein unpack_file_id use hota hai
    file_id_parts = unpack_file_id(media.file_id)
    
    # file_ref (bytes) is crucial for persistent storage
    file_ref = file_id_parts.file_reference
    
    return {
        "file_id": media.file_id,                      # Original ID
        "file_unique_id": media.file_unique_id,        # Unique ID for duplicate check
        "file_ref": file_ref,                          # Permanent File Reference (bytes)
        "file_name": media.file_name,
        "file_size": media.file_size,
        "file_type": media.media.value,                # 'video', 'document', 'audio'
        "caption": media.caption or ""                 # Caption ko empty string rakha hai
    }

# --- 2. save_file Function (Asli Saving) ---
async def save_file(media):
    details = get_file_details(media)
    if not details:
        return 'error'

    # Clean Name Logic: Replace common separators with space for better search
    # Yeh cleaning Text Index ke saath use karne ke liye zaroori nahi,
    # lekin Regex search ke liye faydemand hai.
    clean_name = re.sub(r"(_|\-|\.|\+)", " ", details['file_name']).lower().strip()
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
    
    # --- Search Query Filtering ---
    # User ki query ko search-friendly banana. (.*?) wildcard ki tarah kaam karta hai.
    query_regex = re.escape(query).replace(" ", ".*?") 
    
    # Base Filter (Case-insensitive search in file_name)
    filter_query = {
        "file_name": {"$regex": query_regex, "$options": "i"} 
    }

    # Optional: File Type Filter
    if file_type:
        filter_query["file_type"] = file_type
        
    # Agar aap Text Index use kar rahe hain, toh aap seedha yeh use kar sakte hain (Zyada efficient):
    # filter_query = {"$text": {"$search": query}} 
    
    
    cursor = files_collection.find(filter_query).sort("_id", 1).skip(offset).limit(max_results)
    
    results = await cursor.to_list(length=max_results)
    total_count = await files_collection.count_documents(filter_query)
    
    # 
    
    return results, total_count

# --- Skip ID Functions (For Indexing Progress) ---
# Skip ID ko database mein save/get karne ke liye (same as previous)
# ... (get_current_skip_id, set_new_skip_id functions yahan aayenge)

