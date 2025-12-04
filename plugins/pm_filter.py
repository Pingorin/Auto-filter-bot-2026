import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from typing import List, Optional, Tuple, Dict, Any

# लोकल फ़ाइलें आयात करें
from database.ia_filterdb import get_search_results, get_file_details, get_available_qualities, get_available_years
from config import Config 

# --- Spell Check Logic ---
async def advantage_spell_chok(message: Message) -> Optional[str]:
    """Gemini API का उपयोग करके स्पेलिंग चेक का अनुकरण (simulate) करता है।"""
    query = message.text
    if not Config.SPELL_CHECK_ENABLED:
        return None
    
    # Placeholder: Real logic requires external LLM API call
    if "spydrman" in query.lower():
        corrected_query = query.lower().replace("spydrman", "Spider-Man").title()
        return corrected_query
        
    return None

# --- Helper Function: Search with Filters ---
async def search_with_filters(
    query: str, 
    quality: Optional[str] = None, 
    year: Optional[int] = None
) -> List[Any]:
    """क्वेरी, क्वालिटी, और वर्ष के साथ डेटाबेस खोज करता है।"""
    # ia_filterdb में get_search_results को फ़िल्टर पैरामीटर्स के साथ कॉल करें
    return await get_search_results(query, quality=quality, year=year, limit=50)


# --- Helper Function: Get File Message ---
async def get_file_message(client: Client, file_id: str) -> Optional[Message]:
    """File ID के आधार पर Telegram से फ़ाइल मैसेज प्राप्त करता है।"""
    media_obj = await get_file_details(file_id)
    if not media_obj:
        return None
    
    try:
        # File Reference का उपयोग करके फ़ाइल प्राप्त करें
        message = await client.get_messages(
            chat_id=int(media_obj.f_storage_path),
            message_ids=int(media_obj._id.split("_")[-1]),
            replies=0
        )
        return message
    except Exception as e:
        print(f"❌ Error fetching message for file {file_id}: {e}")
        return None

# --- Helper Function: Display Results and Filters ---
async def display_search_results(
    client: Client, 
    msg: Message, 
    query: str, 
    results: List[Any], 
    page: int = 0, 
    quality: Optional[str] = None, 
    year: Optional[int] = None,
    is_spell_check: bool = False,
    is_edit: bool = False
):
    """खोज परिणामों को Inline Buttons के रूप में प्रदर्शित करता है।"""
    
    total_results = len(results)
    start_index = page * Config.MAX_BUTTONS
    end_index = start_index + Config.MAX_BUTTONS
    current_results = results[start_index:end_index]
    
    if not current_results and is_edit:
        # पेज खाली है, लेकिन पहले से संदेश मौजूद है
        await client.answer_callback_query(msg.id, "इस फ़िल्टर के साथ कोई परिणाम नहीं।")
        return 

    # Buttons का निर्माण
    buttons = []
    for media_obj in current_results:
        callback_data = f"getfile#{media_obj._id}" 
        file_name_display = media_obj.file_name
        file_size_display = round(media_obj.file_size / (1024 * 1024), 2)
        
        buttons.append(
            InlineKeyboardButton(
                text=f"{file_name_display} ({file_size_display} MB)",
                callback_data=callback_data
            )
        )
    
    # Pagination Buttons
    # Callback data format: 'page#<query>#<page>#<quality>#<year>'
    encoded_query = query.replace('#', '##') 
    current_filters = f"{quality or 'None'}#{year or 'None'}"
    
    pagination_buttons = []
    if start_index > 0:
        pagination_buttons.append(
            InlineKeyboardButton("⬅️ पिछला", callback_data=f"page#{encoded_query}#{page - 1}#{current_filters}")
        )
    if end_index < total_results:
        pagination_buttons.append(
            InlineKeyboardButton("अगला ➡️", callback_data=f"page#{encoded_query}#{page + 1}#{current_filters}")
        )
        
    # Filter Menu Button
    filter_buttons = [
        InlineKeyboardButton(
            text=f"⚙️ फ़िल्टर ({quality or 'All'} | {year or 'All'})", 
            callback_data=f"filter_menu#{encoded_query}#{page}#{current_filters}"
        )
    ]
    
    inline_markup = []
    for i in range(0, len(buttons), Config.MAX_BUTTONS):
        inline_markup.append(buttons[i:i + Config.MAX_BUTTONS])
        
    if pagination_buttons:
        inline_markup.append(pagination_buttons)
        
    inline_markup.append(filter_buttons)
        
    # Message Text
    header = "🔮 **स्पेल चेक परिणाम**" if is_spell_check else "📚 **खोज परिणाम**"
    
    text = (
        f"{header}\n\n"
        f"क्वेरी: `{query}`\n"
        f"सक्रिय फ़िल्टर: Quality=`{quality or 'All'}`, Year=`{year or 'All'}`\n"
        f"कुल परिणाम: `{total_results}`\n\n"
        f"परिणाम {start_index + 1} से {min(end_index, total_results)} तक प्रदर्शित हो रहे हैं।"
    )
    
    # Reply या Edit करें
    if is_edit:
        await msg.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_markup),
            disable_web_page_preview=True
        )
    else:
        await msg.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_markup),
            disable_web_page_preview=True
        )

# --- Auto Filter Core Function ---
async def auto_filter(client: Client, msg: Message, spoll: bool = True):
    """उपयोगकर्ता की खोज क्वेरी को संसाधित (process) करता है।"""
    query = str(msg.text).strip()
    if not query: return
    query = re.sub(r'/(page|p)\s*\d+$', '', query, flags=re.IGNORECASE)

    # Core search (नो-फ़िल्टर)
    search_results = await search_with_filters(query) 

    # Spell Check
    if not search_results and spoll:
        corrected_query = await advantage_spell_chok(msg)
        
        if corrected_query:
            spell_check_results = await search_with_filters(corrected_query)
            
            if spell_check_results:
                await display_search_results(
                    client, msg, corrected_query, spell_check_results, is_spell_check=True
                )
                return
            
    # Final Result Display
    if search_results:
        await display_search_results(client, msg, query, search_results)
    else:
        await msg.reply_text(
            f"❌ **खोज परिणाम नहीं मिले**\n\n"
            f"क्वेरी: `{query}`\n"
            "कृपया अपनी क्वेरी में स्पेलिंग जांचें या कुछ अलग खोजें।"
        )

# --- MESSAGE HANDLERS ---
@Client.on_message(filters.text & filters.private & ~filters.command)
async def pm_search_handler(client: Client, message: Message):
    """Private messages में Auto-Filter को ट्रिगर करता है।"""
    await auto_filter(client, message, spoll=True)

@Client.on_message(filters.text & filters.group & ~filters.command)
async def group_search_handler(client: Client, message: Message):
    """Groups में Auto-Filter को ट्रिगर करता है।"""
    if len(message.text) > 5:
        await auto_filter(client, message, spoll=False)

# --- CALLBACK QUERY HANDLERS ---

# 1. Get File Callback
@Client.on_callback_query(filters.regex("^getfile#"))
async def get_file_callback(client: Client, callback_query: CallbackQuery):
    file_id = callback_query.data.split("#")[1]
    await callback_query.answer("⏳ फ़ाइल प्राप्त कर रहा हूँ...", show_alert=False)
    file_msg = await get_file_message(client, file_id)
    
    if file_msg:
        try:
            await file_msg.copy(callback_query.message.chat.id)
            await callback_query.message.delete()
        except Exception as e:
            await callback_query.message.reply_text(f"❌ फ़ाइल अग्रेषित करने में त्रुटि आई: {e}")
    else:
        await callback_query.message.reply_text("❌ फ़ाइल डेटाबेस में नहीं मिली या चैनल से डिलीट हो चुकी है।")
        
# 2. Pagination Callback (page#...)
@Client.on_callback_query(filters.regex("^page#"))
async def next_page_cb_handler(client: Client, callback_query: CallbackQuery):
    # 'page#<encoded_query>#<page>#<quality>#<year>'
    data = callback_query.data.split("#")
    encoded_query, new_page_str, quality, year = data[1], data[2], data[3], data[4]
    
    query = encoded_query.replace('##', '#')
    new_page = int(new_page_str)
    quality_filter = quality if quality != 'None' else None
    year_filter = int(year) if year != 'None' and year.isdigit() else None
    
    await callback_query.answer("🔄 पेज लोड हो रहा है...", show_alert=False)
    
    search_results = await search_with_filters(query, quality_filter, year_filter)

    if search_results:
        await display_search_results(
            client, callback_query.message, query, search_results, 
            new_page, quality_filter, year_filter, is_edit=True
        )
    else:
        await callback_query.message.edit_text("❌ परिणाम लोड करने में त्रुटि आई या कोई परिणाम नहीं मिला।")

# 3. Filter Menu Callback (filter_menu#...)
@Client.on_callback_query(filters.regex("^filter_menu#"))
async def filter_menu_cb_handler(client: Client, callback_query: CallbackQuery):
    # 'filter_menu#<encoded_query>#<page>#<quality>#<year>'
    data = callback_query.data.split("#")
    encoded_query, page, quality, year = data[1], data[2], data[3], data[4]
    
    await callback_query.answer("फ़िल्टर मेनू", show_alert=False)
    
    # Menu Buttons
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="✨ क्वालिटी फ़िल्टर", 
                callback_data=f"quality_filter#{encoded_query}#{page}#{quality}#{year}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 वर्ष फ़िल्टर", 
                callback_data=f"year_filter#{encoded_query}#{page}#{quality}#{year}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ परिणाम पर वापस", 
                callback_data=f"page#{encoded_query}#{page}#{quality}#{year}"
            )
        ]
    ])
    
    await callback_query.message.edit_text(
        "⚙️ **फ़िल्टर मेनू**\n\nविकल्प चुनें:",
        reply_markup=buttons
    )

# 4. Quality Filter List Callback (quality_filter#...)
@Client.on_callback_query(filters.regex("^quality_filter#"))
async def quality_filter_cb_handler(client: Client, callback_query: CallbackQuery):
    # 'quality_filter#<encoded_query>#<page>#<quality>#<year>'
    data = callback_query.data.split("#")
    encoded_query, page, current_quality, year = data[1], data[2], data[3], data[4]
    
    await callback_query.answer("क्वालिटी सूची लोड हो रही है...", show_alert=False)
    qualities = await get_available_qualities()
    quality_buttons = []
    
    quality_buttons.append(
        InlineKeyboardButton(
            text=f"{'✅ ' if current_quality == 'None' else ''}सभी क्वालिटी (All)",
            callback_data=f"setq#{encoded_query}#{page}#None#{year}"
        )
    )

    for q in qualities:
        is_selected = q == current_quality
        quality_buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_selected else ''}{q}",
                callback_data=f"setq#{encoded_query}#{page}#{q}#{year}"
            )
        )
        
    inline_markup = []
    for i in range(0, len(quality_buttons), 2):
        inline_markup.append(quality_buttons[i:i+2])
        
    inline_markup.append([
        InlineKeyboardButton("⬅️ वापस फ़िल्टर मेनू", callback_data=f"filter_menu#{encoded_query}#{page}#{current_quality}#{year}")
    ])
    
    await callback_query.message.edit_text(
        "✨ **क्वालिटी फ़िल्टर**\n\nवह क्वालिटी चुनें:",
        reply_markup=InlineKeyboardMarkup(inline_markup)
    )

# 5. Year Filter List Callback (year_filter#...)
@Client.on_callback_query(filters.regex("^year_filter#"))
async def year_filter_cb_handler(client: Client, callback_query: CallbackQuery):
    # 'year_filter#<encoded_query>#<page>#<quality>#<year>'
    data = callback_query.data.split("#")
    encoded_query, page, quality, current_year = data[1], data[2], data[3], data[4]
    
    await callback_query.answer("वर्ष सूची लोड हो रही है...", show_alert=False)
    years = await get_available_years() 
    year_buttons = []
    
    year_buttons.append(
        InlineKeyboardButton(
            text=f"{'✅ ' if current_year == 'None' else ''}सभी वर्ष (All)",
            callback_data=f"sety#{encoded_query}#{page}#{quality}#None"
        )
    )

    for y in years:
        y_str = str(y)
        is_selected = y_str == current_year
        year_buttons.append(
            InlineKeyboardButton(
                text=f"{'✅ ' if is_selected else ''}{y_str}",
                callback_data=f"sety#{encoded_query}#{page}#{quality}#{y_str}"
            )
        )
        
    inline_markup = []
    for i in range(0, len(year_buttons), 4):
        inline_markup.append(year_buttons[i:i+4])
        
    inline_markup.append([
        InlineKeyboardButton("⬅️ वापस फ़िल्टर मेनू", callback_data=f"filter_menu#{encoded_query}#{page}#{quality}#{current_year}")
    ])
    
    await callback_query.message.edit_text(
        "📅 **वर्ष फ़िल्टर**\n\nवह वर्ष चुनें:",
        reply_markup=InlineKeyboardMarkup(inline_markup)
    )

# 6. Set Quality Callback (setq#...)
@Client.on_callback_query(filters.regex("^setq#"))
async def set_quality_cb_handler(client: Client, callback_query: CallbackQuery):
    # 'setq#<encoded_query>#<page>#<new_quality>#<year>'
    data = callback_query.data.split("#")
    encoded_query, page, new_quality, year = data[1], data[2], data[3], data[4]
    
    query = encoded_query.replace('##', '#')
    quality = new_quality if new_quality != 'None' else None
    year_filter = int(year) if year != 'None' and year.isdigit() else None
    
    await callback_query.answer(f"Quality सेट कर रहा हूँ: {quality or 'All'}", show_alert=False)
    
    search_results = await search_with_filters(query, quality=quality, year=year_filter)
    
    if search_results:
        await display_search_results(
            client, callback_query.message, query, search_results, 
            page=0, quality=quality, year=year_filter, is_edit=True
        )
    else:
        await callback_query.answer("❌ इस फ़िल्टर के साथ कोई परिणाम नहीं मिला।", show_alert=True)
        await filter_menu_cb_handler(client, callback_query) # वापस मेनू दिखाएं


# 7. Set Year Callback (sety#...)
@Client.on_callback_query(filters.regex("^sety#"))
async def set_year_cb_handler(client: Client, callback_query: CallbackQuery):
    # 'sety#<encoded_query>#<page>#<quality>#<new_year>'
    data = callback_query.data.split("#")
    encoded_query, page, quality, new_year = data[1], data[2], data[3], data[4]
    
    query = encoded_query.replace('##', '#')
    quality_filter = quality if quality != 'None' else None
    year = int(new_year) if new_year != 'None' and new_year.isdigit() else None
    
    await callback_query.answer(f"Year सेट कर रहा हूँ: {year or 'All'}", show_alert=False)
    
    search_results = await search_with_filters(query, quality=quality_filter, year=year)
    
    if search_results:
        await display_search_results(
            client, callback_query.message, query, search_results, 
            page=0, quality=quality_filter, year=year, is_edit=True
        )
    else:
        await callback_query.answer("❌ इस फ़िल्टर के साथ कोई परिणाम नहीं मिला।", show_alert=True)
        await filter_menu_cb_handler(client, callback_query) # वापस मेनू दिखाएं


# 8. Advantage Spell Choker Callback (spoll#...)
@Client.on_callback_query(filters.regex("^spoll#"))
async def advantage_spoll_choker_cb_handler(client: Client, callback_query: CallbackQuery):
    # 'spoll#<corrected_query>'
    corrected_query = callback_query.data.split("#")[1]
    await callback_query.answer("सुधार लागू हो रहा है...", show_alert=False)
    
    search_results = await search_with_filters(corrected_query)
    
    if search_results:
        await display_search_results(
            client, callback_query.message, corrected_query, search_results, 
            is_spell_check=True, is_edit=True
        )
    else:
        await callback_query.message.edit_text("❌ सुधारित क्वेरी के लिए भी कोई परिणाम नहीं मिला।")
