# database/ia_filterdb.py
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from pyrogram.file_id import FileId

# MongoDB Connection
client = AsyncIOMotorClient(Config.DB_URI)
db = client["IndexingBotDB"]
files_collection = db["files"] # Main collection for indexed files
settings_collection = db["settings"] # Collection for global settings like skip ID

# --- 1. File Saving Function ---
async def save_file(media):
    """Saves a file's details into the database."""
    file_id = media.file_id
    file_unique_id = media.file_unique_id
    file_name = media.file_name
    file_size = media.file_size
    
    # Check for duplicate
    duplicate_check = await files_collection.find_one({"file_unique_id": file_unique_id})
    if duplicate_check:
        return 'duplicate'

    # Prepare data
    data = {
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "file_name": file_name,
        "file_size": file_size,
        "media_type": media.media.value
        # Future: Add caption, channel ID etc.
    }
    
    try:
        await files_collection.insert_one(data)
        return 'success'
    except Exception as e:
        print(f"Error saving file: {e}")
        return 'error'

# --- 2. Skip ID Functions ---
# Skip ID ko database mein save/get karne ke liye
async def get_current_skip_id():
    setting = await settings_collection.find_one({"_id": "skip_id"})
    return setting.get("value", Config.DEFAULT_SKIP_ID) if setting else Config.DEFAULT_SKIP_ID

async def set_new_skip_id(new_id):
    await settings_collection.update_one(
        {"_id": "skip_id"},
        {"$set": {"value": new_id}},
        upsert=True
    )
