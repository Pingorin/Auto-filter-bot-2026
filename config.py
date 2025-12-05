import os

class Config:
    # Ensure API_ID is an integer. Default to 0 if missing.
    try:
        API_ID = int(os.environ.get("API_ID", "0"))
    except ValueError:
        API_ID = 0
        print("Error: API_ID must be an Integer.")

    API_HASH = os.environ.get("API_HASH", "")
    
    # Bot Token
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # Database URI
    DB_URI = os.environ.get("DB_URI", "")
    
    # Optional links
    CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannelUsername")
    OWNER_LINK = os.environ.get("OWNER_LINK", "https://t.me/YourOwnerUsername")
