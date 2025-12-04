import os
from typing import List

class Config:
    """
    टेलीग्राम बॉट और डेटाबेस के लिए सभी कॉन्फ़िगरेशन सेटिंग्स, 
    जो Heroku Config Vars/Environment Variables से पढ़ी जाती हैं।
    """
    
    # --- Telegram Bot Credentials ---
    # API ID: Integer. अगर नहीं मिला तो 0 default माना जाएगा।
    API_ID: int = int(os.environ.get("API_ID", 0)) 
    
    # API HASH: String
    API_HASH: str = os.environ.get("API_HASH", "")  
    
    # BOT TOKEN: String
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "") 

    # Admin IDs (multiple IDs separated by spaces, e.g., "123 456")
    # Admin IDs environment variable से read किए जाते हैं
    ADMINS: List[int] = [
        int(x.strip()) 
        for x in os.environ.get("ADMINS", "").split() 
        if x.strip().isdigit()
    ]
    
    # --- Database Settings (MongoDB) ---
    # DB_URI: MongoDB Connection String (User's preferred name)
    DB_URI: str = os.environ.get("DB_URI", "")
    DATABASE_NAME: str = os.environ.get("DATABASE_NAME", "filter_bot_db")
    COLLECTION_NAME: str = os.environ.get("COLLECTION_NAME", "media_files")
    
    # --- Links and Bot Info ---
    CHANNEL_LINK: str = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannelUsername")
    OWNER_LINK: str = os.environ.get("OWNER_LINK", "https://t.me/YourOwnerUsername")
    
    # --- Search and Filter Settings ---
    # MAX_BUTTONS: एक पंक्ति में अधिकतम इनलाइन बटन
    MAX_BUTTONS: int = int(os.environ.get("MAX_BUTTONS", 4)) 
    # SPELL_CHECK_ENABLED: स्पेल चेक को सक्षम/अक्षम करें (True/False)
    SPELL_CHECK_ENABLED: bool = os.environ.get("SPELL_CHECK_ENABLED", "True").lower() in ('true', '1', 't')

    # Logging Channel ID: Integer
    LOG_CHANNEL: int = int(os.environ.get("LOG_CHANNEL", 0))
    
    print("Configuration loaded from Environment Variables.")
