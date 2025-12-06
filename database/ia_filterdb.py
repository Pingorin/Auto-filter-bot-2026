import motor.motor_asyncio
from info import DATABASE_URI

class MediaDB:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.files

    async def ensure_indexes(self):
        # Search fast karne ke liye
        await self.col.create_index([("file_name", "text")])

Media = MediaDB(DATABASE_URI, "MyBotDB")
