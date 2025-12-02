import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import config  # Humari config file import kar rahe hain

# Logging setup (Debug karne ke liye)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # --- Buttons Setup ---
    
    # 1. Add me to your groups (Deep link logic)
    # Format: https://t.me/BOT_USERNAME?startgroup=true
    add_group_url = f"https://t.me/{config.BOT_USERNAME}?startgroup=true"
    
    keyboard = [
        [
            # Row 1: Add to group button
            InlineKeyboardButton("➕ Add me to your groups", url=add_group_url)
        ],
        [
            # Row 2: Main Channel aur Bot Owner side-by-side
            InlineKeyboardButton("📢 Main Channel", url=config.CHANNEL_LINK),
            InlineKeyboardButton("👤 Bot Owner", url=config.OWNER_LINK)
        ],
        [
            # Row 3: About Button (Yeh callback trigger karega, URL nahi kholega)
            InlineKeyboardButton("ℹ️ About", callback_data='about_info')
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # User ko message bhejna
    await update.message.reply_text(
        f"Hello {user.first_name}! 👋\n\n"
        "Main ek advanced Python bot hoon. Niche diye gaye buttons check karein:",
        reply_markup=reply_markup
    )

# 'About' button dabane par kya hoga uska function
async def about_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # Button click acknowledge karna (loading hatane ke liye)
    await query.answer()
    
    # Message edit karke about info dikhana ya naya message bhejna
    # Yahan hum naya message bhej rahe hain
    await query.message.reply_text(
        "ℹ️ **About This Bot**\n\n"
        "Yeh bot Python aur python-telegram-bot library se bana hai.\n"
        "Developer: Aapka Naam",
        parse_mode='Markdown'
    )

if __name__ == '__main__':
    # Application build karna
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    # Handlers add karna
    start_handler = CommandHandler('start', start)
    about_handler = CallbackQueryHandler(about_button, pattern='about_info')
    
    application.add_handler(start_handler)
    application.add_handler(about_handler)
    
    print("Bot start ho gaya hai...")
    # Bot ko run karna
    application.run_polling()
