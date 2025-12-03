# bot.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# --- Database Setup (MongoDB) ---
mongo_client = AsyncIOMotorClient(Config.DB_URI)
db = mongo_client["MyTelegramBotDB"] # Database ka naam
groups_collection = db["groups"]     # Collection jahan groups save honge

# --- Bot Client Setup ---
app = Client(
    "my_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# --- Helper Function: Save Group to DB ---
async def add_group_to_db(group_id, group_name, added_by_user_id):
    # Upsert logic: Agar group pehle se hai to update karega, nahi to naya banayega
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
    print(f"Saved Group: {group_name} ({group_id})")

# --- 1. /start Command Handler ---
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    # Bot ka username fetch karte hain taaki 'Add me' link ban sake
    bot_info = await client.get_me()
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
            # 📣 Main Channel
            InlineKeyboardButton(
                text="📣 Main Channel",
                url=Config.CHANNEL_LINK
            ),
            # 🧑‍💻 Bot Owner
            InlineKeyboardButton(
                text="🧑‍💻 Bot Owner",
                url=Config.OWNER_LINK
            )
        ],
        [
            # ℹ️ About
            InlineKeyboardButton(
                text="ℹ️ About",
                callback_data="about_info"
            )
        ]
    ])

    await message.reply_text(
        text=f"👋 Hello {message.from_user.first_name}!\n\nMain ek advanced group management bot hoon. Neeche diye gaye buttons use karein.",
        reply_markup=buttons
    )

# --- 2. Callback Handler (About Button) ---
@app.on_callback_query(filters.regex("about_info"))
async def about_callback(client: Client, callback_query: CallbackQuery):
    info_text = (
        "**🤖 Bot Information**\n\n"
        "Version: 1.0\n"
        "Framework: Pyrogram & MongoDB\n"
        "Feature: Group Tracking System\n\n"
        "Yeh bot groups ko manage aur track karne ke liye banaya gaya hai."
    )
    await callback_query.answer(info_text, show_alert=True)

# --- 3. New Chat Members Handler (DB Saving Logic) ---
# Jab bot kisi naye group mein add hota hai
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    bot_id = (await client.get_me()).id
    
    for member in message.new_chat_members:
        # Check karein agar naya member khud BOT hai
        if member.id == bot_id:
            group_id = message.chat.id
            group_name = message.chat.title
            added_by = message.from_user.id if message.from_user else None
            
            # Database mein save karein
            await add_group_to_db(group_id, group_name, added_by)
            
            await message.reply_text(
                f"Thanks for adding me to **{group_name}**!\nI have saved this group to my database."
            )

# --- Bot Run ---
print("Bot Started...")
app.run()
