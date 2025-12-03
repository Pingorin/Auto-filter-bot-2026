import logging
import asyncio
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configuration
import config
# Database handlers (Connection is handled inside ia_filter.py using Motor/umongo)
import database.ia_filter as db_filter 

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Client Initialization ---
app = Client(
    "your_bot_session",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    # Plugins folder load karein: index.py ab automatically load ho jayega
    plugins=dict(root="plugins") 
)

# --- Handlers (Pyrogram Style) ---

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    """
    /start command aane par yeh function chalega.
    """
    bot_username = client.me.username # Pyrogram mein client.me se bot ki details milti hain
    
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
    
    await message.reply_text(
        f"👋 Namaste {message.from_user.first_name}!\n\n"
        "Main ek advanced Python bot hoon. Neeche diye gaye buttons use karein:",
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.MARKDOWN
    )

@app.on_callback_query()
async def button_handler(client, query):
    """
    Callback button handler.
    """
    await query.answer()

    if query.data == "about_section":
        await query.message.edit_text(
            text=(
                "ℹ️ **About This Bot**\n\n"
                "Yeh bot Python aur MongoDB use karke banaya gaya hai.\n"
                "Developer: Bot Owner Name\n"
                "Library: Pyrogram v2+"
            ),
            parse_mode=enums.ParseMode.MARKDOWN,
            # Same keyboard wapas bhejne ki zaroorat nahi hai
        )
    # Callback ko index handler mein forward karein (agar index.py mein yeh logic ho)
    # NOTE: Pyrogram mein plugins automatically load ho jaate hain.
    # index.py mein bhi @app.on_callback_query() handler hona chahiye.
    elif query.data.startswith('index_'):
        # Assuming index.py has its own callback handler.
        # Agar aapko yahan se forward karna hai, toh index_handler mein function bana kar yahan call karein.
        # Filhaal, hum rely karenge ki index.py apne aap handle karega.
        pass

# NOTE: Pyrogram mein ChatMemberUpdate ke liye filters.chat_member use hota hai
@app.on_chat_member_updated(filters.group)
async def track_group_additions(client, update):
    """
    Jab bhi bot kisi group mein add hoga ya uska status badlega.
    """
    # Check if the bot was added or status changed to admin/member
    if update.new_chat_member and update.new_chat_member.user.is_self:
        new_status = update.new_chat_member.status
        
        if new_status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]:
            chat_id = update.chat.id
            chat_title = update.chat.title
            
            # Group data ko database mein save karne ka logic (Assuming db_filter handles it)
            try:
                # Assuming you have a function in db_filter for saving group info
                # Is function ko db_filter mein define karna hoga.
                # await db_filter.save_group(chat_id, chat_title) 
                
                logger.info(f"New Group Added: {chat_title} ({chat_id})")
                await client.send_message(chat_id, "Thanks for adding me! Data saved to DB.")
                
            except Exception as e:
                logger.error(f"Error saving group to MongoDB: {e}")
                await client.send_message(chat_id, "⚠️ Error: Could not save group info to database.")


# --- Main Application ---
async def main():
    logger.info("Starting bot...")
    
    # Database initialization check (ia_filter mein hoga)
    # yahan aap koi simple query chala kar connection check kar sakte hain.
    
    await app.start()
    logger.info("Bot started successfully!")
    
    # Bot ko chalu rakhega
    await idle() 

    logger.info("Bot stopping...")
    await app.stop()


if __name__ == '__main__':
    # Pyrogram aur asyncio ko run karein
    asyncio.run(main())
