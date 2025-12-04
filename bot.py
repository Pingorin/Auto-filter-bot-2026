from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient 
from config import Config

# --- Database Setup (MongoDB) ---
try:
    mongo_client = AsyncIOMotorClient(Config.DB_URI)
    db = mongo_client["MyTelegramBotDB"]
    # Globally available collection variable
    groups_collection = db["groups"]
    print("MongoDB Client Initialized.")
except Exception as e:
    print(f"Error initializing MongoDB Client: {e}")
    pass 


# --- Bot Client Setup with PLUGINS ---
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
    print("Bot is shutting down...")
    app.stop()
    # Close MongoDB connection safely
    try:
        mongo_client.close() 
    except NameError:
        pass 
    print("Bot Stopped and DB connection closed.")
