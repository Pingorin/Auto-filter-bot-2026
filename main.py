import os
import logging
import pyrogram 
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
filter_col = db["files"] # 'files' कलेक्शन का नाम

# Pyrogram Client Instance बनाएं
app = Client(
    "AutoFilterBot", # सेशन नेम
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=50,
    plugins={"root": "plugins"} # प्लगइन लोडिंग यहाँ है
)

# Note: /start, /id, और अन्य कमांड हैंडलर्स अब plugins/commands.py में हैं।

# --- AUTO FILTER LOGIC ---
@app.on_message(filters.text & filters.private)
async def auto_filter_handler(client: Client, message: Message):
    # खाली या बहुत छोटे मैसेज को अनदेखा करें
    if len(message.text) < 3:
        return
        
    query = message.text.lower().strip()
    
    # MongoDB में फ़ाइलों को खोजें (Indexing Logic के बाद काम करेगा)
    cursor = filter_col.find(
        {'file_name': {'$regex': query, '$options': 'i'}}
    ).limit(5)
    
    results = [document async for document in cursor]
    
    if results:
        # अगर परिणाम मिले, तो Inline Buttons दिखाएँ
        buttons = []
        for file in results:
            buttons.append(
                [InlineKeyboardButton(text=f"📂 {file.get('file_name', 'Unknown File')}", 
                                      # 'file_id' और 'unique_id' को Indexing के बाद उपयोग किया जाएगा
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
if __name__ == "__main__":
    # app.run() Pyrogram को ब्लॉक करता है और उसे चलता रखता है।
    # यह Heroku पर 24/7 चलने का सबसे आसान और सबसे विश्वसनीय तरीका है।
    # Pyrogram शुरू करने से पहले MongoDB से कनेक्शन की जाँच करने का लॉजिक अब app.run() के अंदर ही किया जाएगा।
    try:
        app.run()
    except Exception as e:
        logger.error(f"बॉट स्टार्टअप त्रुटि: {e}")
