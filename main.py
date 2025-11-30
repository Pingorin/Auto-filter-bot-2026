from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import logging

# Logging सेट करें ताकि आप बॉट की गतिविधि देख सकें
logging.basicConfig(level=logging.INFO)

# Pyrogram Client Instance बनाएं
app = Client(
    "AutoFilterBot", # सेशन नेम
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins={"root": "plugins"} # प्लगइन्स के लिए फ़ोल्डर
)

# Start Command Handler
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        f"👋 नमस्ते, **{message.from_user.mention}**!\n"
        "मैं एक Auto Filter Bot हूँ। मैं आपके चैनल की फ़ाइलों को ढूँढ़ने में मदद कर सकता हूँ।"
    )

# जब बॉट स्टार्ट हो
async def main():
    print("बॉट शुरू हो रहा है...")
    await app.start()
    me = await app.get_me()
    print(f"✅ बॉट सफलतापूर्वक शुरू हुआ: @{me.username}")
    await app.stop() # यह लाइन हटा देंगे जब हम इसे 24/7 चलाएंगे, अभी सिर्फ टेस्टिंग के लिए
    
# इसे चलाएं
if __name__ == "__main__":
    app.run(main()) 
