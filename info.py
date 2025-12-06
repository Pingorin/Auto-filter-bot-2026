import os

# Mandatory Variables
API_ID = int(os.environ.get("API_ID", "")) # Apna API ID daalein agar local run kar rahe hain
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DATABASE_URI = os.environ.get("DATABASE_URI", "")

# Optional
ADMINS = [int(i) for i in os.environ.get("ADMINS", "").split(" ")] if os.environ.get("ADMINS") else []
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", ""))
PORT = int(os.environ.get("PORT", "8080"))
