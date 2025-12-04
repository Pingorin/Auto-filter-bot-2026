from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# --- Database Setup ---
mongo_client = AsyncIOMotorClient(Config.DB_URI)
db = mongo_client["MyTelegramBotDB"]

# --- Bot Client Setup with PLUGINS ---
# plugins=dict(root="plugins") line zaroori hai @Client decorator ke liye
app = Client(
    "my_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins") 
)

# --- Bot Run ---
print("Bot Started with Plugins...")

try:
    app.run()
except KeyboardInterrupt:
    app.stop()
    print("Bot Stopped.")
