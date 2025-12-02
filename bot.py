# bot.py
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ChatMemberHandler
from pymongo import MongoClient
import config

# Logging setup (Debug ke liye)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# MongoDB Connection Setup
cluster = MongoClient(config.MONGO_URL)
db = cluster["TelegramBotDB"]
groups_collection = db["groups"]

# --- Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start command aane par yeh function chalega.
    Yeh 4 buttons show karega.
    """
    bot_username = context.bot.username
    
    # Buttons Create karna
    keyboard = [
        [
            # Button 1: Add to Group (URL Button with startgroup parameter)
            InlineKeyboardButton(
                "➕ Add me to your groups", 
                url=f"https://t.me/{bot_username}?startgroup=true"
            )
        ],
        [
            # Button 2 & 3: Channel and Owner
            InlineKeyboardButton("📢 Main Channel", url=config.CHANNEL_LINK),
            InlineKeyboardButton("👤 Bot Owner", url=config.OWNER_LINK)
        ],
        [
            # Button 4: About (Callback Button)
            InlineKeyboardButton("ℹ️ About", callback_data="about_section")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Namaste {update.effective_user.first_name}!\n\n"
        "Main ek advanced Python bot hoon. Neeche diye gaye buttons use karein:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Jab koi 'About' button dabayega, yeh function chalega.
    """
    query = update.callback_query
    await query.answer() # Button click animation stop karne ke liye

    if query.data == "about_section":
        await query.edit_message_text(
            text=(
                "ℹ️ **About This Bot**\n\n"
                "Yeh bot Python aur MongoDB use karke banaya gaya hai.\n"
                "Developer: Bot Owner Name\n"
                "Library: python-telegram-bot v20+"
            ),
            parse_mode="Markdown"
        )

async def track_group_additions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Yeh sabse important part hai.
    Jab bhi bot kisi group mein add hoga, yeh function trigger hoga
    aur group ka data MongoDB mein save karega.
    """
    result = update.my_chat_member
    new_member = result.new_chat_member
    
    # Check karein ki kya bot ko group me add kiya gaya hai?
    if new_member.status in ["member", "administrator"]:
        chat_id = result.chat.id
        chat_title = result.chat.title
        username = result.chat.username
        
        # Data structure jo DB me save hoga
        group_data = {
            "_id": chat_id, # Duplicate se bachne ke liye ID ko primary key banaya
            "title": chat_title,
            "username": username,
            "added_on": result.date
        }
        
        try:
            # upsert=True ka matlab: agar exist karta hai to update karo, nahi to naya banao
            groups_collection.update_one(
                {"_id": chat_id}, 
                {"$set": group_data}, 
                upsert=True
            )
            logging.info(f"New Group Saved to MongoDB: {chat_title}")
            
            # Optional: Group me Hello message bhejna
            await context.bot.send_message(chat_id, "Thanks for adding me! Data saved to DB.")
            
        except Exception as e:
            logging.error(f"Error saving to MongoDB: {e}")

# --- Main Application ---

if __name__ == '__main__':
    # Bot Application Build karein
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Handlers Add karein
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # ChatMemberHandler: Jab bot ka status group me change ho (add/remove)
    application.add_handler(ChatMemberHandler(track_group_additions, ChatMemberHandler.MY_CHAT_MEMBER))

    print("Bot is running...")
    # Bot ko run karein
    application.run_polling()
