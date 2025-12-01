import os
from dotenv import load_dotenv

# .env file se variables load karein (optional, lekin achha practice)
load_dotenv() 

class Config:
    # Telegram API Credentials
    # Inhe Telegram my.telegram.org se praapt karein
    API_ID = int(os.environ.get("API_ID", 123456)) 
    API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")

    # Bot Token (@BotFather se)
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN") 
    
    # MongoDB Atlas Connection String
    # Format: mongodb+srv://username:password@clustername.mongodb.net/
    DATABASE_URI = os.environ.get("DATABASE_URI", "YOUR_MONGODB_URI")
    
    # Admins List (Apna User ID)
    # Aap ek se zyada IDs bhi rakh sakte hain
    ADMINS = [int(id) for id in os.environ.get("ADMINS", "123456789").split()] 
    
    # Bot ke liye database ka naam
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "Indexing_Bot_DB")
