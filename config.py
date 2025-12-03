# config.py

import os

class Config:
    # Saare credentials Heroku ke Config Vars/Environment se read honge
    
    # API ID: Integer hona chahiye
    # Note: os.environ.get() string deta hai, isliye int() mein wrap kiya hai.
    API_ID = int(os.environ.get("API_ID", )) 
    
    # API HASH: String
    API_HASH = os.environ.get("API_HASH", "")  
    
    # BOT TOKEN: String
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 

    # MongoDB Connection String: String
    DB_URI = os.environ.get("DB_URI", "")
    
    # Links: Yeh bhi environment se read kiye ja sakte hain
    CHANNEL_LINK = os.environ.get("CHANNEL_LINK", "https://t.me/YourChannelUsername")
    OWNER_LINK = os.environ.get("OWNER_LINK", "https://t.me/YourOwnerUsername")
