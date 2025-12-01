import asyncio
from pyrogram import Client
from info import Config
from motor.motor_asyncio import AsyncIOMotorClient
from umongo.frameworks.motor import MotorCollection
from umongo import Instance

# MongoDB Client aur umongo Instance setup
# Connect DB
class Bot(Client):
    def __init__(self):
        super().__init__(
            "IndexerBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins"), # Plugins folder se handlers load karega
            sleep_threshold=10,
        )
        self.db = None
        self.db_instance = None

    async def start(self):
        await super().start()
        print("Connecting to MongoDB...")
        
        # MongoDB Connection
        self.motor_client = AsyncIOMotorClient(Config.DATABASE_URI)
        self.db = self.motor_client[Config.DATABASE_NAME]
        self.db_instance = Instance(self.db)
        print("Bot Started! 🚀")

    async def stop(self, *args):
        await super().stop()
        print("Bot Stopped!")


if __name__ == "__main__":
    bot = Bot()
    bot.run()
