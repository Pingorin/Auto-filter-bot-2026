import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ChatMemberHandler
from pymongo import MongoClient
import config

# Modular Handler Import:
# Indexing aur filtering ka sara logic ab is file mein hoga
import plugins.index as index_handler 
import database.ia_filter as db_filter
# NOTE: Make sure 'plugins' and 'database' are directories in your project root.

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- MongoDB Connection Setup (Global Access) ---
try:
    cluster = MongoClient(config.MONGO_URL, serverSelectionTimeoutMS=5000)
    cluster.admin.command('ping') # Connection check
    db = cluster[config.DATABASE_NAME] # Config me DATABASE_NAME zaroor set karein
    groups_collection = db["groups"]
    logging.info("MongoDB Connection Successful.")
except Exception as e:
    logging.error(f"MongoDB Connection Failed: {e}")
    db = None
    groups_collection = None


# --- Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start command aane par yeh function chalega.
    """
    if not update.message: return
    bot_username = context.bot.username
    
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Add me to your groups", 
                url=f"https://t.me/{bot_username}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton("📢 Main Channel", url=config.CHANNEL_LINK),
            InlineKeyboardButton("👤 Bot Owner", url=config.OWNER_LINK)
        ],
        [
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
    Callback button handler.
    """
    query = update.callback_query
    await query.answer()

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
    # Forward Callback to Index Handler (agar index se related ho)
    elif query.data.startswith('index_'):
        await index_handler.index_callback_handler(update, context)

async def track_group_additions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Jab bhi bot kisi group mein add hoga, yeh function trigger hoga
    aur group ka data MongoDB mein save karega.
    """
    if not groups_collection:
        logging.warning("Group tracking skipped: MongoDB not connected.")
        return

    result = update.my_chat_member
    new_member = result.new_chat_member
    
    if new_member.status in ["member", "administrator"]:
        chat_id = result.chat.id
        chat_title = result.chat.title
        username = result.chat.username
        
        group_data = {
            "_id": chat_id,
            "title": chat_title,
            "username": username,
            "added_on": result.date
        }
        
        try:
            groups_collection.update_one(
                {"_id": chat_id}, 
                {"$set": group_data}, 
                upsert=True
            )
            logging.info(f"New Group Saved to MongoDB: {chat_title}")
            await context.bot.send_message(chat_id, "Thanks for adding me! Data saved to DB.")
            
        except Exception as e:
            logging.error(f"Error saving group to MongoDB: {e}")


# --- Main Application ---

if __name__ == '__main__':
    # Ensure database is connected before running bot
    if not db:
        logging.critical("Exiting: Cannot run bot without database connection.")
        exit(1)
        
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Handlers Add karein
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('index', index_handler.index_command)) # New Index Handler
    
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(ChatMemberHandler(track_group_additions, ChatMemberHandler.MY_CHAT_MEMBER))

    print("Bot is running...")
    application.run_polling()
