from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# लोकल फ़ाइलें आयात करें
from config import Config
from database.ia_filterdb import media_collection, get_available_qualities, get_available_years
from bot import LOGGER, app # bot.py से app और LOGGER को आयात करें
from plugins.index import is_admin 

# --- 1. /start Command Handler (अब यहाँ है) ---
@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    """स्टार्ट कमांड का जवाब देता है और बटन दिखाता है।"""
    
    # DEBUGGING LOG: संदेश प्राप्ति की पुष्टि
    user_name = message.from_user.first_name if message.from_user else "Unknown"
    LOGGER.info(f"'/start' command received from user: {message.from_user.id} ({user_name}) in command.py")
    
    try:
        # बॉट की जानकारी app client से प्राप्त करें
        bot_info = await app.get_me()
        bot_username = bot_info.username
        
        # Buttons Create karna
        buttons = InlineKeyboardMarkup([
            [
                # ➕ Add me to your groups
                InlineKeyboardButton(
                    text="➕ Add me to your groups",
                    url=f"https://t.me/{bot_username}?startgroup=true"
                )
            ],
            [
                # 📣 Main Channel (Config.CHANNEL_LINK आवश्यक)
                InlineKeyboardButton(
                    text="📣 Main Channel",
                    url=Config.CHANNEL_LINK
                ),
                # 🧑‍💻 Bot Owner (Config.OWNER_LINK आवश्यक)
                InlineKeyboardButton(
                    text="🧑‍💻 Bot Owner",
                    url=Config.OWNER_LINK
                )
            ],
            [
                # ℹ️ About
                InlineKeyboardButton(
                    text="ℹ️ About",
                    callback_data="about_info" # यह callback bot.py में हैंडल होगा
                )
            ]
        ])

        await message.reply_text(
            text=f"👋 Hello {message.from_user.first_name}!\n\nMain ek advanced group management bot hoon. Neeche diye gaye buttons use karein.",
            reply_markup=buttons
        )
        LOGGER.info(f"Successfully sent /start response to {user_name} from command.py.")

    except Exception as e:
        LOGGER.error(f"❌ ERROR in /start handler in command.py for user {message.from_user.id}: {e}")
        try:
            await message.reply_text(f"🚨 कमांड निष्पादित करने में आंतरिक त्रुटि आई: {e}")
        except:
            pass


# --- 2. /total_files Command Handler (Admin) ---
@Client.on_message(filters.command("total_files") & filters.private)
async def total_files_handler(client: Client, message: Message):
    """एडमिन को डेटाबेस में इंडेक्स की गई फ़ाइलों की कुल संख्या दिखाता है।"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("❌ यह कमांड केवल मेरे एडमिन के लिए है।")
        return

    if not media_collection:
        await message.reply_text("🚨 डेटाबेस कनेक्शन उपलब्ध नहीं है।")
        return
        
    try:
        count = await media_collection.count_documents({"is_deleted": False})
        
        await message.reply_text(
            f"📊 **फ़ाइल सांख्यिकी (File Statistics)**\n\n"
            f"सक्रिय रूप से इंडेक्स की गई फ़ाइलें: `{count}`"
        )
        
    except Exception as e:
        await message.reply_text(f"❌ सांख्यिकी प्राप्त करने में त्रुटि आई: {e}")


# --- 3. /filters Command Handler (General/Admin) ---
@Client.on_message(filters.command("filters") & filters.private)
async def filters_handler(client: Client, message: Message):
    """उपलब्ध फ़िल्टरिंग विकल्प (जैसे Quality, Year) दिखाता है।"""
    try:
        qualities = await get_available_qualities()
        years = await get_available_years()
        
        qualities_str = ", ".join(qualities) if qualities else "कोई नहीं"
        years_str = ", ".join(map(str, years)) if years else "कोई नहीं"
        
        text = (
            "⚙️ **उपलब्ध फ़िल्टर**\n\n"
            "आप अपनी खोज में इन फ़िल्टर का उपयोग कर सकते हैं:\n\n"
            f"✨ **क्वालिटी (Quality):** `{qualities_str}`\n"
            f"📅 **वर्ष (Year):** `{years_str}`\n\n"
            "उदाहरण के लिए: `Avengers 720p 2012`"
        )
        
        await message.reply_text(text)
        
    except Exception as e:
        await message.reply_text(f"❌ फ़िल्टर जानकारी प्राप्त करने में त्रुटि आई: {e}")
