from pyrogram import Client, errors
from config import Config
from database import mongo_client 

# --- Bot Client Setup (Refactored to Class) ---
class Bot(Client):
    def __init__(self):
        # Initialize the Pyrogram client using configuration values
        super().__init__(
            name='aks',
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            # Custom parameters as requested
            sleep_threshold=5,
            workers=150,
            # Ensure plugins are still loaded
            plugins={"root": "plugins"}
        )

# Instantiate the Bot class
app = Bot()

# --- Bot Run ---
if __name__ == "__main__":
    print("Bot Started with Plugins...")
    try:
        app.run()
    except errors.FloodWait as e:
        print(f"❌ FLOOD WAIT ERROR: You must wait {e.value} seconds before starting the bot again.")
        print("Please stop the bot and try again later.")
    except KeyboardInterrupt:
        print("Bot is shutting down...")
    finally:
        # Stop the app if running
        try:
            if app.is_connected:
                app.stop()
        except:
            pass
            
        # Close DB Connection safely using the imported client
        try:
            mongo_client.close()
            print("MongoDB connection closed.")
        except Exception as e:
            print(f"Error closing DB: {e}")
