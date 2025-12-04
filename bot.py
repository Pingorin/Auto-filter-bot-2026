from pyrogram import Client
from config import Config
# Import mongo_client from the new file just to close it safely
from database import mongo_client 

# --- Bot Client Setup ---
app = Client(
    "my_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins") 
)

# --- Bot Run ---
if __name__ == "__main__":
    print("Bot Started with Plugins...")
    try:
        app.run()
    except KeyboardInterrupt:
        print("Bot is shutting down...")
    finally:
        # Stop the app if running
        try:
            if app.is_connected:
                app.stop()
        except:
            pass
            
        # Close DB Connection
        try:
            mongo_client.close()
            print("MongoDB connection closed.")
        except Exception as e:
            print(f"Error closing DB: {e}")
