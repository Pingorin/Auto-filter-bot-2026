import os
import logging
import pyrogram 
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Logging सेट करें
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- GLOBAL CLIENTS ---
# MongoDB क्लाइंट और डेटाबेस इंस्टेंस
# यह कनेक्शन बॉट के चलने के दौरान बना रहेगा
DB_CLIENT = AsyncIOMotorClient(Config.DATABASE_URI)
db = DB_CLIENT["filter_bot"] 
filter_col = db["files"] 

# Pyrogram Client Instance बनाएं
app = Client(
    "AutoFilterBot", # सेशन नेम
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=50,
    plugins={"root": "plugins"} # plugins फ़ोल्डर लोड करें
)

# --- AUTO FILTER LOGIC (Temporary Filter) ---
# यह सिर्फ़ एक डिफ़ॉल्ट हैंडलर है। इसे आप plugins/filter_handlers.py में ले जा सकती हैं।
@app.on_message(filters.text & filters.private)
async def auto_filter_handler(client: Client, message: Message):
    if len(message.text) < 3:
        return
        
    # Heroku लॉग्स में मैसेज रिसीविंग की जांच के लिए लॉग
    logger.info(f"Received filter query from {message.from_user.id}: {message.text}")
    
    # यहाँ फ़िल्टरिंग लॉजिक आएगा
    await message.reply_text("🔍 आपकी फ़ाइल खोजी जा रही है...")


# --- CORE FUNCTION: BOT STARTUP ---

# यह सुनिश्चित करता है कि कोड तभी चले जब फ़ाइल सीधे रन की जाए
if __name__ == "__main__":
    try:
        # MongoDB कनेक्शन चेक
        if Config.DATABASE_URI:
            logger.info("MongoDB कनेक्शन की जाँच हो रही है...")
            DB_CLIENT.admin.command('ping')
            logger.info("✅ MongoDB से सफलतापूर्वक कनेक्टेड।")
        else:
             logger.warning("❌ DATABASE_URI सेट नहीं है। फ़ाइल इंडेक्सिंग काम नहीं करेगी।")

        # app.run() Pyrogram को शुरू करता है और Heroku पर चलता रखता है
        app.run() 
        
    except Exception as e:
        logger.error(f"❌ बॉट शुरू करने में अंतिम त्रुटि: {e}")
