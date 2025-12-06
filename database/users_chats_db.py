import motor.motor_asyncio
from info import DATABASE_URI

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    async def get_banned(self):
        # Dummy function to prevent errors initially
        return [], []

    async def add_user(self, id):
        user = await self.col.find_one({'id': int(id)})
        if not user:
            await self.col.insert_one({'id': int(id)})

db = Database(DATABASE_URI, "MyBotDB")
