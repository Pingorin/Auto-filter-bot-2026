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

# --- AUTO FILTER LOGIC ---
# filters.command को एक्सक्लूड (Exclude) करें ताकि यह केवल फ़िल्टरिंग टेक्स्ट पर काम करे।
# यह सुनिश्चित करता है कि /start, /id, आदि पर यह फ़ंक्शन नहीं चलता है।
@app.on_message(filters.text & filters.private & ~filters.command(["start", "index", "id"])) 
async def auto_filter_handler(client: Client, message: Message):
    if len(message.text) < 3:
        # यह सिर्फ़ छोटे मैसेज (जैसे 'The' या एक अक्षर) को अनदेखा करेगा
        return
        
    query = message.text.lower().strip()
    
    # यह लॉग यह सुनिश्चित करेगा कि हम जानते हैं कि यह ट्रिगर हुआ है
    logger.info(f"Received filter query from {message.from_user.id}: {message.text}")
    
    # यहाँ असली फ़िल्टरिंग लॉजिक आएगा (जो अभी सिर्फ़ डिफ़ॉल्ट जवाब दे रहा है)
    await message.reply_text("🔍 आपकी फ़ाइल खोजी जा रही है...")


# --- CORE FUNCTION: BOT STARTUP ---

if __name__ == "__main__":
    try:
        # MongoDB कनेक्शन चेक (सिर्फ़ शुरुआत में)
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
