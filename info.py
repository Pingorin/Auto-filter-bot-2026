import os

# Mandatory Variables
API_ID = int(os.environ.get("API_ID", "12345")) # Apna API ID daalein agar local run kar rahe hain
API_HASH = os.environ.get("API_HASH", "apna_hash_yahan")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "apna_bot_token")
DATABASE_URI = os.environ.get("DATABASE_URI", "apna_mongodb_url")

# Optional
ADMINS = [int(i) for i in os.environ.get("ADMINS", "").split(" ")] if os.environ.get("ADMINS") else []
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-100xxxx"))
PORT = int(os.environ.get("PORT", "8080"))
