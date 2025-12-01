# Bot information and configuration variables
# These are the default values, which can be overridden by Environment Variables.

# --- Bot Information ---
BOT_VERSION = "3.1.0"
OWNER_ID = 123456789  # Replace with your Telegram User ID
BOT_NAME = "MyPythonBot"

# --- Strings/Messages ---
START_MESSAGE_HTML = (
    "<b>नमस्ते {}!</b>\n\n"
    "मैं एक Python-आधारित Telegram Bot हूँ।\n"
    "मुझे Heroku पर डिप्लॉय किया गया है और मैं डेटा के लिए MongoDB का उपयोग करता हूँ।"
)

# --- Other Configurations ---
MAX_FILE_SIZE_MB = 50
