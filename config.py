# config.py

import os

class Config:
    # Saare credentials Environment/Config Vars se read honge
    
    # --- Telegram Credentials ---
    # API ID: Integer hona chahiye
    # Note: os.environ.get() string deta hai, isliye int() mein wrap kiya hai.
    # Default value '0' diya gaya hai agar environment variable set na ho
    API_ID = int(os.environ.get("API_ID", 0)) 
    
    # API HASH: String
    API_HASH = os.environ.get("API_HASH", "")  
    
    # BOT TOKEN: String
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 

    # --- Database Credentials ---
    # MongoDB Connection String: String
    DB_URI = os.environ.get("DB_URI", "")
    
    # --- Bot Configuration and Indexing Settings ---
    
    # Admin IDs: Space/Comma separated string in Config Vars.
    # Yeh list of integers banata hai
    ADMINS = [
        int(i) 
        for i in os.environ.get(
            "ADMINS", 
            "123456789" # Default Admin ID
        ).split()
    ]
    
    # Log Channel ID: Indexing requests aur errors yahan aayenge
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -100123456789))
    
    # Caption Filter: True/False. Kya search karte waqt file caption bhi check karna hai?
    # os.environ.get() se string (True/False) read hoga, use bool mein convert kiya gaya hai.
    USE_CAPTION_FILTER = os.environ.get("USE_CAPTION_FILTER", "True").lower() == "true"
    
    # Default Skip ID: Indexing kahan se shuru ho
    DEFAULT_SKIP_ID = int(os.environ.get("DEFAULT_SKIP_ID", 1)) # Default 1 se shuru
    
    # --- Links ---
    CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannelUsername")
    OWNER_LINK = os.environ.get("OWNER_LINK", "https://t.me/YourOwnerUsername")
