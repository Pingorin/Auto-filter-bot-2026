from pyrogram import Client, filters
from pyrogram.types import Message

# लोकल फ़ाइलें आयात करें
from config import Config
from database.ia_filterdb import media_collection, get_available_qualities, get_available_years

# index.py से admin helper फ़ंक्शन आयात करें
from plugins.index import is_admin 

# --- /start Command Handler (हटा दिया गया) ---
# NOTE: /start command handler को bot.py में रखा गया है ताकि बटन दिखाई दें। 
#       यहाँ से इसे हटाने पर कॉन्फ़्लिक्ट खत्म हो जाएगा।
#
# @Client.on_message(filters.command("start") & filters.private)
# async def start_handler(client: Client, message: Message):
#     """स्टार्ट कमांड का जवाब देता है।"""
#     ... (यह कोड हटाया गया है)


# --- 1. /total_files Command Handler (Admin) ---
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


# --- 2. /filters Command Handler (General/Admin) ---
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
