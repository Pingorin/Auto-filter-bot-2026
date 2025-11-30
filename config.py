import os
from dotenv import load_dotenv

# .env फ़ाइल से लोकल वेरिएबल्स लोड करें
load_dotenv() 

class Config:
    # 1. Telegram API Details 
    # हम सुनिश्चित कर रहे हैं कि वेरिएबल मौजूद हो (या डिफ़ॉल्ट रूप से None हो)
    API_ID_STR = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    
    # Check if API_ID_STR exists before converting to int
    if API_ID_STR and API_ID_STR.isdigit():
        API_ID = int(API_ID_STR)
    else:
        # अगर API_ID सेट नहीं है या नंबर नहीं है, तो बॉट शुरू नहीं होगा।
        # हम इसे 0 सेट कर रहे हैं ताकि कोड चले, लेकिन बॉट क्रैश हो जाएगा।
        print("❌ WARNING: API_ID is missing or invalid in Config Vars.")
        API_ID = 0 
        
    # 2. Bot Token
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    
    # 3. MongoDB URI - Auto Filter के लिए ज़रूरी
    DATABASE_URI = os.environ.get("DATABASE_URI")
    
    # 4. Admin User IDs (सुरक्षित रूप से लिस्ट लोड करें)
    # यह सुनिश्चित करता है कि अगर खाली हो तो भी क्रैश न हो।
    ADMINS_STR = os.environ.get("ADMINS", "")
    ADMINS = [int(x.strip()) for x in ADMINS_STR.split() if x.strip().isdigit()]
    
    # 5. Channel IDs (सुरक्षित रूप से लिस्ट लोड करें)
    CHANNELS_STR = os.environ.get("CHANNELS", "")
    CHANNELS = [int(x.strip()) for x in CHANNELS_STR.split() if x.strip().isdigit()]
