from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient 
from config import Config

# --- Database Setup (MongoDB) ---
# Initialize DB connection only once here
try:
    mongo_client = AsyncIOMotorClient(Config.DB_URI)
    db = mongo_client["MyTelegramBotDB"]
    # This globally available collection variable will be used in the handlers
    groups_collection = db["groups"]
    print("MongoDB Client Initialized.")
except Exception as e:
    print(f"Error initializing MongoDB Client: {e}")
    # Allow bot to continue running even if DB fails initially
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
