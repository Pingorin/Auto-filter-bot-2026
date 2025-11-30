import os
import logging
import pyrogram 
import asyncio
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

# 1. Pyrogram BOT Client Instance (मैसेज हैंडलिंग के लिए)
app = Client(
    "AutoFilterBot", # सेशन नेम
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=50,
    plugins={"root": "plugins"} # plugins फ़ोल्डर लोड करें
)

# 2. Pyrogram USER Client Instance (चैनल हिस्ट्री पढ़ने के लिए)
# USER_SESSION को Config Vars से पढ़ें
USER_SESSION = os.environ.get("USER_SESSION")

if USER_SESSION and Config.API_ID != 0:
    logger.info("यूज़र क्लाइंट शुरू करने के लिए तैयार है।")
    user_client = Client(
        USER_SESSION, # सेशन स्ट्रिंग
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        no_updates=True, # इसे मैसेज अपडेट न सुनने दें
        in_memory=True # डिस्क पर कोई .session फ़ाइल न बनाएं
    )
else:
    logger.warning("❌ USER_SESSION Config Var सेट नहीं है। इंडेक्सिंग काम नहीं करेगी।")
    # अगर सेशन नहीं है, तो user_client को None पर सेट करें
    user_client = None 

# --- AUTO FILTER LOGIC ---
# यह हैंडलर कमांड्स को अनदेखा करेगा (जो plugins/commands.py में है)
@app.on_message(filters.text & filters.private & ~filters.command(["start", "index", "id"])) 
async def auto_filter_handler(client: Client, message: Message):
    if len(message.text) < 3:
        return
        
    logger.info(f"Received filter query from {message.from_user.id}: {message.text}")
    
    # यहाँ फ़िल्टरिंग/सर्च लॉजिक आएगा
    await message.reply_text("🔍 आपकी फ़ाइल खोजी जा रही है...") 


# --- CORE FUNCTION: BOT STARTUP ---

async def start_all():
    logger.info("बॉट शुरू हो रहा है...")

    # MongoDB कनेक्शन चेक
    if Config.DATABASE_URI:
        try:
            await DB_CLIENT.admin.command('ping')
            logger.info("✅ MongoDB से सफलतापूर्वक कनेक्टेड।")
        except Exception:
            logger.error("❌ MongoDB कनेक्शन त्रुटि।")

    # Bot Client को शुरू करें
    await app.start()
    me = await app.get_me()
    logger.info(f"✅ बॉट सफलतापूर्वक शुरू हुआ: @{me.username}")
    
    # User Client को शुरू करें (यदि मौजूद है)
    if user_client:
        try:
            await user_client.start()
            user_me = await user_client.get_me()
            logger.info(f"✅ यूज़र क्लाइंट सफलतापूर्वक शुरू हुआ: @{user_me.username}")
        except Exception as e:
            logger.error(f"❌ यूज़र क्लाइंट शुरू करने में त्रुटि: {e}")
            
    # बॉट को 24/7 चलता रहने दें
    await pyrogram.idle() 
    
    # बॉट बंद होने पर साफ़-सफ़ाई
    await app.stop()
    if user_client:
        await user_client.stop() 

# main फ़ाइल रनर
if __name__ == "__main__":
    asyncio.run(start_all())
