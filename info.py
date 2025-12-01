# info.py (Correct way to use environment variables)
import os
# ...
class Config:
    API_ID = int(os.environ.get("API_ID", "123456")) 
    API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN") 
    DATABASE_URI = os.environ.get("DATABASE_URI", "YOUR_MONGODB_URI")
    # ...
