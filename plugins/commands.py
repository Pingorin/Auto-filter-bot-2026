from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import logging

logger = logging.getLogger(__name__)

# Start Command Handler
# filters.command("start") को filters.regex("^/start") से बदलें
# यह हमेशा /start से शुरू होने वाले मैसेज को पकड़ेगा, भले ही Telegram उसे कमांड के रूप में न भेजे।
@Client.on_message(filters.regex("^/start") & filters.private)
async def start_handler(client: Client, message: Message):
    
    # Heroku लॉग्स में मैसेज रिसीविंग की जांच के लिए लॉग
    logger.info(f"Received /start from {message.from_user.id} in chat {message.chat.id}")
    
    if message.from_user.id in Config.ADMINS:
        text = "👋 नमस्ते, **एडमिन**!\n\nफ़ाइलों को इंडेक्स करने के लिए `/index` कमांड (जल्द ही) का उपयोग करें।"
    else:
        text = f"👋 नमस्ते, **{message.from_user.mention}**!\n\nमैं एक Auto Filter Bot हूँ। बस फ़ाइल का नाम टाइप करें, मैं उसे आपके लिए ढूँढ़ने की कोशिश करूँगा।"

    try:
        # सुनिश्चित करें कि बॉट reply_text का उपयोग कर रहा है
        await message.reply_text(text)
    except Exception as e:
        logger.error(f"Error replying to start command: {e}")


# Get ID Command Handler 
@Client.on_message(filters.command("id") & filters.private)
async def get_id_handler(client: Client, message: Message):
    user_id = message.from_user.id
    await message.reply_text(f"आपका Telegram Numeric ID है: `{user_id}`")
