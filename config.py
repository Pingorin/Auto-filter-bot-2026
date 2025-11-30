import os
from dotenv import load_dotenv

# .env फ़ाइल से लोकल वेरिएबल्स लोड करें
load_dotenv() 

class Config:
    # Telegram API Details (Heroku Config Vars या .env से)
    API_ID = int(os.environ.get("20638104"))
    API_HASH = os.environ.get("6c884690ca85d39a4c5ad7c15b194e42")
    
    # Bot Token
    BOT_TOKEN = os.environ.get("8504476517:AAHfyOVpPuWyWtgh-mY4Uh6zIoSK7J1CbkI")
    
    # MongoDB URI - Auto Filter के लिए ज़रूरी
    DATABASE_URI = os.environ.get("mongodb+srv://anu77:anu77@cluster0.8ohtzju.mongodb.net/")
    
    # Admin User IDs (आपकी ID - अगर एक से ज़्यादा हैं, तो उन्हें स्पेस से अलग करें)
    # हम स्ट्रिंग को लिस्ट में बदल रहे हैं
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "7245547751").split()] 
    
    # Channel IDs (फ़िल्टर करने के लिए)
    CHANNELS = [int(x) for x in os.environ.get("CHANNELS", "").split()]
