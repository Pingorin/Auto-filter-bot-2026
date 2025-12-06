import logging
from struct import pack
import re
from pyrogram.file_id import FileId
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI

class MediaDB:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.files

    async def ensure_indexes(self):
        # Search fast karne ke liye Indexing
        await self.col.create_index([("file_name", "text")])

    async def save_file(self, media):
        """File ko database mein save karta hai"""
        try:
            file_id = media.file_id
            file_name = media.file_name
            file_size = media.file_size
            
            # Check agar file pehle se hai
            file = await self.col.find_one({'file_id': file_id})
            if file:
                return False
            
            # Nayi file save karein
            await self.col.insert_one({
                'file_id': file_id,
                'file_name': file_name,
                'file_size': file_size,
                'caption': media.caption.html if media.caption else None,
                'file_type': media.mime_type
            })
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    async def get_search_results(self, query):
        """Database se milti-julti files dhoondhta hai"""
        regex = re.compile(query, re.IGNORECASE)
        filter = {"file_name": regex}
        
        # Files dhoondho aur limit lagao (Max 10 for now)
        cursor = self.col.find(filter)
        cursor.sort('$natural', -1) # Latest files pehle
        
        files = await cursor.to_list(length=10)
        return files

# Database Object initialize karein
Media = MediaDB(DATABASE_URI, "MyBotDB")
