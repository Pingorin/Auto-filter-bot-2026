import os
import logging
import pyrogram # NameError को ठीक करने के लिए
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
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
filter_col = db["files"] # 'files' यहाँ कलेक्शन का नाम है

# Pyrogram Client Instance बनाएं
app = Client(
    "AutoFilterBot", # सेशन नेम
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=50
)

# --- COMMAND HANDLERS ---

# Start Command Handler
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if message.from_user.id in Config.ADMINS:
        text = "👋 नमस्ते, **एडमिन**!\n\nफ़ाइलों को इंडेक्स करने के लिए `/index` कमांड का उपयोग करें। फ़िलहाल मैं सिर्फ़ `/start` का जवाब दे रहा हूँ।"
    else:
        text = f"👋 नमस्ते, **{message.from_user.mention}**!\n\nमैं एक Auto Filter Bot हूँ। बस फ़ाइल का नाम टाइप करें, मैं उसे आपके लिए ढूँढ़ने की कोशिश करूँगा।"

    await message.reply_text(text)


# --- AUTO FILTER LOGIC ---
@app.on_message(filters.text & filters.private)
async def auto_filter_handler(client: Client, message: Message):
    # खाली या बहुत छोटे मैसेज को अनदेखा करें
    if len(message.text) < 3:
        return
        
    query = message.text.lower().strip()
    
    # MongoDB में फ़ाइलों को खोजें (Query the database)
    # यहाँ हम regex का उपयोग कर रहे हैं (case-insensitive search)
    # ध्यान दें: Indexing logic अभी बाकी है, इसलिए यह अभी खाली परिणाम देगा
    cursor = filter_col.find(
        {'file_name': {'$regex': query, '$options': 'i'}}
    ).limit(5)
    
    # परिणामों को लिस्ट में बदलें
    results = [document async for document in cursor]
    
    if results:
        # अगर परिणाम मिले
        
        # यहाँ आप परिणामों को Inline Buttons के रूप में प्रदर्शित कर सकते हैं
        # उदाहरण के लिए:
        buttons = []
        for file in results:
            # यहाँ आपको फ़ाइल को एक्सेस करने के लिए एक unique ID चाहिए होगी, 
            # जिसे हम Indexing के बाद MongoDB में स्टोर करेंगे।
            # अभी यह सिर्फ डेमो के लिए है।
            buttons.append(
                [InlineKeyboardButton(text=f"📂 {file.get('file_name', 'Unknown File')}", 
                                      callback_data=f"getfile_{file.get('file_id', '0')}")]
            )
            
        buttons.append([InlineKeyboardButton(text="❌ बंद करें", callback_data="close")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            f"🔍 **{len(results)}** परिणाम मिले:",
            reply_markup=reply_markup
        )
        
    else:
        # अगर कोई परिणाम नहीं मिला
        await message.reply_text("कोई परिणाम नहीं मिला। कृपया कुछ और खोजें।")


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
    await pyrogram.idle() 
    
    # बॉट बंद होने पर साफ़-सफ़ाई
    await app.stop() 


if __name__ == "__main__":
    # Python 3.7+ में asyncio.run() का उपयोग करें
    import asyncio
    asyncio.run(main())
