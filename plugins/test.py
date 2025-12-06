from pyrogram import Client, filters
from info import ADMINS

@Client.on_message(filters.command("test") & filters.user(ADMINS))
async def test_channel(bot, message):
    if len(message.command) < 2:
        return await message.reply("Channel ID do! Example: `/test -100xxxx`")

    chat_id = int(message.command[1])
    msg = await message.reply("🕵️ Jaanch kar raha hoon...")

    # 1. Check: Kya Bot Channel mein message Bhej sakta hai?
    try:
        sent = await bot.send_message(chat_id, "Test Message (Checking Permissions)")
        await msg.edit(f"✅ **Write Permission:** OK! (Main message bhej pa raha hoon)")
        # Test message delete kar do taaki kachra na ho
        await sent.delete()
    except Exception as e:
        return await msg.edit(f"❌ **Write Permission:** FAIL!\nMain channel mein message nahi bhej pa raha.\nError: `{e}`\n\n**Solution:** Bot ko channel mein 'Post Messages' ki permission do.")

    # 2. Check: Kya Bot ko Messages Dikh rahe hain?
    count = 0
    details = ""
    
    # Bina kisi filter ke search karo (Empty Query)
    try:
        async for m in bot.search_messages(chat_id, limit=5):
            count += 1
            type_name = "Unknown"
            if m.video: type_name = "Video 🎬"
            elif m.document: type_name = "Document 📁"
            elif m.photo: type_name = "Photo 🖼️"
            elif m.text: type_name = "Text 💬"
            
            details += f"{count}. {type_name} (ID: {m.id})\n"
            
    except Exception as e:
        return await msg.edit(f"❌ **Read Permission:** FAIL!\nSearch mein Error aaya: `{e}`")

    # Result
    if count == 0:
        await msg.edit("❌ **Read Permission:** FAIL! (0 Messages Found)\n\nBot ko channel **Pura Khali** dikh raha hai.\n\n**Solution:**\n1. Channel me ek **Naya** Video abhi upload karo.\n2. Agar fir bhi na dikhe, to Bot ko Admin se hata kar wapis Admin banao.")
    else:
        await msg.edit(f"✅ **Read Permission:** OK!\nBot ne ye messages dekhe:\n\n{details}\n\n**Agar yahan Video/Document hai par Index 0 hai, to Database ki galti hai.**")
