import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from pymongo import MongoClient
from Script import load_plugins # Script.py से प्लगइन्स लोड करने के लिए

# Import your command file from the plugin folder
from plugins.Command import start_command_plugin

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
LOGGER = logging.getLogger(__name__)

# --- Configuration (using Environment Variables) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")

if not BOT_TOKEN or not MONGO_URI:
    LOGGER.error("BOT_TOKEN or MONGO_URI environment variables are not set.")
    exit(1)

# --- Database Connection (MongoDB) ---
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["telegram_bot_db"] # Database Name
    LOGGER.info("Successfully connected to MongoDB.")
except Exception as e:
    LOGGER.error(f"MongoDB connection failed: {e}")
    # Consider what to do if the DB connection fails (e.g., exit or run without DB)

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command and shows the start interface."""
    user = update.effective_user
    
    # Example of how to use a function from a plugin file (Command.py)
    await start_command_plugin(update, context, db) # Pass DB object if needed

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles unknown commands."""
    await update.message.reply_text("क्षमा करें, मैं इस कमांड को नहीं पहचानता।")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Add Handlers ---
    application.add_handler(CommandHandler("start", start))

    # Add other handlers (e.g., from Script.py or other plugin files)
    # application.add_handler(CommandHandler("help", help_command)) 

    # Handle unknown commands last
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    LOGGER.info("Starting bot with Polling...")
    # For Heroku deployment, Webhooks are often preferred, but Polling works too.
    # We use Polling here for simplicity.
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
