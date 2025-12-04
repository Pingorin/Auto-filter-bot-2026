import motor.motor_asyncio
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import time

# --- 1. Media Class/Schema ---
@dataclass
class Media:
    """
    इंडेक्स की गई फ़ाइलों के लिए डेटाबेस मॉडल (स्कीमा)।
    """
    _id: str
    file_id: str
    file_ref: bytes
    file_name: str
    file_size: int
    caption: str
    f_storage_path: str # Telegram chat ID
    mime_type: str
    quality: Optional[str] = None
    year: Optional[int] = None
    date: Optional[float] = time.time()
    is_deleted: bool = False

# --- Database Initialization ---
media_collection: Optional[motor.motor_asyncio.AsyncIOMotorCollection] = None

async def init_db_connection(db_uri: str, db_name: str, collection_name: str):
    """MongoDB कलेक्शन ऑब्जेक्ट को इनिशियलाइज़ करता है।"""
    global media_collection
    try:
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(db_uri)
        db = mongo_client[db_name]
        media_collection = db[collection_name]
        # फ़ाइल नाम और caption पर इंडेक्सिंग सेट करें ताकि खोज तेज हो
        await media_collection.create_index([
            ("file_name", motor.motor_asyncio.TEXT), 
            ("caption", motor.motor_asyncio.TEXT)
        ], name="text_search_index")
        print("✅ Database collection initialized successfully and indexes created.")
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        media_collection = None

# --- 2. Database Interaction Functions (Core Logic) ---

async def save_file_in_db(media_data: Media) -> Optional[bool]:
    """एक नई फ़ाइल को डेटाबेस में सेव या अपडेट करता है।"""
    if not media_collection: return None
    try:
        await media_collection.update_one(
            {"_id": media_data._id},
            {"$set": media_data.__dict__},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"❌ Error saving file {media_data.file_name}: {e}")
        return None

async def get_file_details(file_id: str) -> Optional[Media]:
    """फ़ाइल ID के आधार पर फ़ाइल के विवरण को डेटाबेस से प्राप्त करता है।"""
    if not media_collection: return None
    try:
        document = await media_collection.find_one({"_id": file_id, "is_deleted": False})
        if document:
            return Media(**document)
        return None
    except Exception as e:
        print(f"❌ Error fetching file details for {file_id}: {e}")
        return None

async def delete_file_from_db(file_id: str) -> Optional[bool]:
    """फ़ाइल को डेटाबेस से सॉफ्ट डिलीट (is_deleted=True सेट) करता है।"""
    if not media_collection: return None
    try:
        result = await media_collection.update_one(
            {"_id": file_id},
            {"$set": {"is_deleted": True}}
        )
        return result.modified_count == 1
    except Exception as e:
        print(f"❌ Error soft deleting file {file_id}: {e}")
        return None

async def get_search_results(query: str, quality: Optional[str] = None, year: Optional[int] = None, limit: int = 50) -> List[Media]:
    """
    दी गई क्वेरी के आधार पर फ़ाइल के नाम और कैप्शन में खोज करता है (फ़िल्टर के साथ)।
    """
    if not media_collection: return []
    
    # $text index का उपयोग करें, अगर text index उपलब्ध हो
    # अगर query में स्पेस है, तो बेहतर परिणाम के लिए $search का उपयोग करें
    find_query = {
        "is_deleted": False, # केवल सक्रिय फ़ाइलें दिखाएं
        "$text": {"$search": query}
    }
    
    # क्वालिटी फ़िल्टर जोड़ें
    if quality:
        find_query["quality"] = quality
        
    # वर्ष फ़िल्टर जोड़ें
    if year:
        find_query["year"] = year

    try:
        # $text search के साथ score का उपयोग करके sort करें, फिर date से
        cursor = media_collection.find(find_query, {"score": {"$meta": "textScore"}}) \
                                 .sort([("score", {"$meta": "textScore"}), ("date", -1)]) \
                                 .limit(limit)
        
        results = [Media(**doc) async for doc in cursor]
        return results
    except Exception as e:
        print(f"❌ Error fetching search results: {e}")
        # अगर $text index नहीं है, तो fallback के रूप में $regex का उपयोग करें
        if "$text" in str(e):
             print("Falling back to $regex search...")
             return await get_search_results_regex_fallback(query, quality, year, limit)
        return []

async def get_search_results_regex_fallback(query: str, quality: Optional[str] = None, year: Optional[int] = None, limit: int = 50) -> List[Media]:
    """Regex आधारित Fallback search (धीमा हो सकता है)।"""
    if not media_collection: return []
    regex_query = {"$regex": query, "$options": "i"}
    
    find_query = {
        "is_deleted": False,
        "$or": [
            {"file_name": regex_query},
            {"caption": regex_query}
        ]
    }
    
    if quality: find_query["quality"] = quality
    if year: find_query["year"] = year

    try:
        cursor = media_collection.find(find_query).sort("date", -1).limit(limit)
        return [Media(**doc) async for doc in cursor]
    except Exception as e:
        print(f"❌ Error in regex search fallback: {e}")
        return []


async def get_available_qualities() -> List[str]:
    """डेटाबेस में मौजूद सभी unique quality values को प्राप्त करता है।"""
    if not media_collection: return []
    try:
        qualities = await media_collection.distinct("quality", {"is_deleted": False, "quality": {"$ne": None}})
        return sorted([q for q in qualities if q and q.strip()])
    except Exception as e:
        print(f"❌ Error fetching available qualities: {e}")
        return []

async def get_available_years() -> List[int]:
    """डेटाबेस में मौजूद सभी unique year values को प्राप्त करता है।"""
    if not media_collection: return []
    try:
        years = await media_collection.distinct("year", {"is_deleted": False, "year": {"$ne": None}})
        return sorted([y for y in years if isinstance(y, int) and y > 1900], reverse=True)
    except Exception as e:
        print(f"❌ Error fetching available years: {e}")
        return []

async def get_bad_files(limit: int = 100) -> List[Media]:
    """उन फ़ाइलों को प्राप्त करता है जिन्हें सॉफ्ट-डिलीट के रूप में चिह्नित किया गया है (is_deleted=True)।"""
    if not media_collection: return []
    try:
        find_query = {"is_deleted": True}
        cursor = media_collection.find(find_query).sort("date", 1).limit(limit)
        return [Media(**doc) async for doc in cursor]
    except Exception as e:
        print(f"❌ Error fetching bad files: {e}")
        return []
