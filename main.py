import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from motor.motor_asyncio import AsyncIOMotorClient # MongoDB के लिए

# Logging सेट करें (Set up Logging)
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pyrogram Client Instance बनाएं
app = Client(
    "AutoFilterBot", # सेशन नेम
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=50,  # बेहतर प्रदर्शन (Performance) के लिए वर्कर्स सेट करें
    plugins={"root": "plugins"} # अगर आप बाद में प्लगइन्स जोड़ना चाहें
)

# MongoDB क्लाइंट और डेटाबेस इंस्टेंस
DB_CLIENT = AsyncIOMotorClient(Config.DATABASE_URI)
# 'filter_bot' यहाँ आपके डेटाबेस का नाम है
db = DB_CLIENT["filter_bot"] 
# 'files' यहाँ कलेक्शन का नाम है जहाँ फ़ाइलों का डेटा स्टोर होगा
filter_col = db["files"] 


# --- COMMAND HANDLERS ---

# Start Command Handler
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if message.from_user.id in Config.ADMINS:
        text = "👋 नमस्ते, **एडमिन**! मैं आपका Auto Filter Bot हूँ।\n\nफ़ाइलों को इंडेक्स करना शुरू करने के लिए `/index` कमांड का उपयोग करें (जल्द ही जोड़ेंगे)।"
    else:
        text = f"👋 नमस्ते, **{message.from_user.mention}**!\n\nमैं एक Auto Filter Bot हूँ। बस फ़ाइल का नाम टाइप करें, मैं उसे आपके लिए ढूँढ़ने की कोशिश करूँगा।"

    await message.reply_text(text)

# Get ID Command Handler (यह एडमिन के लिए ID चेक करने में मदद करेगा)
@app.on_message(filters.command("id") & filters.private)
async def get_id_handler(client: Client, message: Message):
    user_id = message.from_user.id
    await message.reply_text(f"आपका Telegram Numeric ID है: `{user_id}`\n\nअगर आप एडमिन हैं, तो इस ID को `ADMINS` Config Var में उपयोग करें।")


# --- CORE FUNCTION: BOT STARTUP ---

async def main():
    logger.info("बॉट शुरू हो रहा है...")
    try:
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ बॉट सफलतापूर्वक शुरू हुआ: @{me.username}")
        
        # MongoDB कनेक्शन चेक
        try:
            await DB_CLIENT.admin.command('ping')
            logger.info("✅ MongoDB से सफलतापूर्वक कनेक्टेड।")
        except Exception as e:
            logger.error(f"❌ MongoDB कनेक्शन त्रुटि: {e}")
            
    except Exception as e:
        logger.error(f"❌ बॉट शुरू करने में त्रुटि: {e}")
    
    # बॉट को 24/7 चलता रहने दें
    # Heroku/Server पर यह आवश्यक है
    await pyrogram.idle() 
    # ^ सुनिश्चित करें कि pyrogram.idle() उपयोग किया गया है, 
    # न कि सिर्फ app.stop(), ताकि बॉट चलता रहे।
    await app.stop() # बॉट बंद होने पर साफ़-सफ़ाई


if __name__ == "__main__":
    # Python 3.7+ में app.run(main()) की जगह app.run(main()) इस्तेमाल होता है
    import asyncio
    asyncio.run(main())
