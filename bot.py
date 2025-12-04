import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import plugins.command # command.py को यहाँ इंपोर्ट करें

# लॉगिंग सेटअप
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

# --- Database Setup (MongoDB) ---
# NOTE: यहाँ 'Config.DB_URI' का उपयोग किया गया है जैसा कि आपके स्निपेट में है।
mongo_client = AsyncIOMotorClient(Config.DB_URI) 
db = mongo_client["MyTelegramBotDB"] # Database ka naam
groups_collection = db["groups"]     # Collection jahan groups save honge

# --- Bot Client Setup ---
app = Client(
    "my_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    in_memory=True # मेमोरी में ही सत्र (session) को रखें
)

# --- Helper Function: Save Group to DB ---
async def add_group_to_db(group_id, group_name, added_by_user_id):
    """Upsert logic: ग्रुप को डेटाबेस में सेव या अपडेट करता है।"""
    await groups_collection.update_one(
        {"_id": group_id},
        {
            "$set": {
                "group_name": group_name,
                "added_by": added_by_user_id,
                "is_active": True
            }
        },
        upsert=True
    )
    LOGGER.info(f"Saved Group: {group_name} ({group_id})")

# --- 1. /start Command Handler Removed from here ---
# /start handler को अब plugins/command.py में शिफ्ट कर दिया गया है।

# --- 2. Callback Handler (About Button) ---
# NOTE: यह callback handler bot.py में ही रहेगा क्योंकि यह सीधे main bot client से जुड़ा है।
@app.on_callback_query(filters.regex("about_info"))
async def about_callback(client: Client, callback_query: CallbackQuery):
    """'About' बटन के लिए जानकारी दिखाता है।"""
    info_text = (
        "**🤖 Bot Information**\n\n"
        "Version: 1.0\n"
        "Framework: Pyrogram & MongoDB\n"
        "Feature: Group Tracking System\n\n"
        "Yeh bot groups ko manage aur track karne ke liye banaya gaya hai."
    )
    # यदि आप इसे एक popup (alert) में नहीं दिखाना चाहते हैं, तो show_alert=True हटा दें
    await callback_query.answer(info_text, show_alert=True)

# --- 3. New Chat Members Handler (DB Saving Logic) ---
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    """जब बॉट किसी नए ग्रुप में ऐड होता है तो ग्रुप डिटेल्स को DB में सेव करता है।"""
    bot_id = (await client.get_me()).id
    
    for member in message.new_chat_members:
        if member.id == bot_id:
            group_id = message.chat.id
            group_name = message.chat.title
            added_by = message.from_user.id if message.from_user else None
            
            # Database mein save karein
            await add_group_to_db(group_id, group_name, added_by)
            
            await message.reply_text(
                f"Thanks for adding me to **{group_name}**!\nI have saved this group to my database."
            )

# --- Main Execution Function ---
async def main():
    """बॉट को शुरू करता है और Pyrogram idle() पर रखता है।"""
    LOGGER.info("Starting Telegram Bot...")
    
    # 1. बॉट क्लाइंट शुरू करें
    await app.start()
    
    # 2. बॉट की जानकारी प्राप्त करें
    bot_info = await app.get_me()
    LOGGER.info(f"Bot Started as @{bot_info.username}")
    
    # 3. बॉट को तब तक चलने दें जब तक कि वह idle न हो
    await idle()
    
    # 4. बॉट क्लाइंट बंद करें
    await app.stop()
    LOGGER.info("Bot stopped.")

# Pyrogram 2.0+ के लिए asyncio.run() का उपयोग करें
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Bot stopped by user interrupt.")
    except Exception as e:
        LOGGER.error(f"An error occurred in main execution: {e}")
