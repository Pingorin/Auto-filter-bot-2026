from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Initialize the client
mongo_client = AsyncIOMotorClient(Config.DB_URI)
db = mongo_client["MyTelegramBotDB"]

# Export this collection so handlers can use it
groups_collection = db["groups"]

print("MongoDB Client Initialized via database.py")
