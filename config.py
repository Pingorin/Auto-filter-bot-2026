import os
from dotenv import load_dotenv

# .env फ़ाइल से लोकल वेरिएबल्स लोड करें (लोकल टेस्टिंग के लिए)
load_dotenv() 

class Config:
    # 1. Telegram API Details 
    API_ID_STR = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    # API ID को int में बदलने की सुरक्षित प्रक्रिया
    if API_ID_STR and API_ID_STR.strip().isdigit():
        API_ID = int(API_ID_STR.strip())
    else:
        # अगर API_ID सेट नहीं है, तो 0 सेट करें (बॉट क्रैश हो जाएगा, लेकिन TypeError नहीं आएगा)
        print("❌ WARNING: API_ID is missing or invalid in Config Vars.")
        API_ID = 0 
        
    # 2. MongoDB URI - Auto Filter के लिए ज़रूरी
    DATABASE_URI = os.environ.get("DATABASE_URI")
    
    # 3. Admin User IDs (आपकी ID - स्पेस से अलग करें)
    # यह सुनिश्चित करता है कि खाली होने पर भी क्रैश न हो।
    ADMINS_STR = os.environ.get("ADMINS", "")
    ADMINS = [int(x.strip()) for x in ADMINS_STR.split() if x.strip().isdigit()]
    
    # 4. Filter Channel IDs (जिन चैनल्स को बॉट इंडेक्स करेगा)
    CHANNELS_STR = os.environ.get("CHANNELS", "")
    CHANNELS = [int(x.strip()) for x in CHANNELS_STR.split() if x.strip() and x.strip().lstrip('-').isdigit()]
