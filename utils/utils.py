import math
from pyrogram.types import InlineKeyboardButton

# 1. File Size ko Human Readable banana (bytes -> MB/GB)
def get_size(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

# 2. Buttons banane ka function
def btn_parser(files):
    buttons = []
    for file in files:
        f_name = file['file_name']
        f_size = get_size(file['file_size'])
        f_id = file['file_id']
        
        # Button Text: [Moviename] [1.2GB]
        btn_text = f"[{f_size}] {f_name}"
        
        # Button par click karne par file ID bhejna
        # Note: 'file_id' bahut lamba hota hai, isliye hum cached ID use karte hain
        # Simple rakhne ke liye hum seedha file bhejenge
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"sendfile#{f_id}")])
        
    return buttons
