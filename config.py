import os

class Config:
    # API ID: Int conversion fixed with default value "0"
    API_ID = int(os.environ.get("API_ID", "")) 
    
    API_HASH = os.environ.get("API_HASH", "")  
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
    DB_URI = os.environ.get("DB_URI", "")
    
    CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannelUsername")
    OWNER_LINK = os.environ.get("OWNER_LINK", "https://t.me/YourOwnerUsername")
