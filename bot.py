import os
import telebot
from telebot import types
from mutagen.id3 import ID3, APIC, TPE1, TALB, TIT2

# --- SOZLAMALAR ---
API_TOKEN = '8158093361:AAE4JR-rZWBNlvY_YOKxHmrOPj1rtqzqZUo'
FIXED_ARTIST = "Mening Kanalim"       # Artist nomi
FIXED_ALBUM = "@kanalingiz_linki"    # Albom nomi
IMAGE_PATH = "cover.jpg"              # GitHub'dagi rasm nomi
# ------------------

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🎵 **Xush kelibsiz!**\nMenga musiqa yuboring, uni tahrirlab beraman.")

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    chat_id = message.chat.id
    temp_file = f"music_{message.audio.file_id}.mp3"
    
    msg = bot.send_message(chat_id, "📥 **Fayl qayta ishlanmoqda...**")
    
    try:
        # Faylni yuklab olish
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(temp_file, 'wb') as f:
            f.write(downloaded_file)

        # Metadatalarni o'zgartirish
        try:
            audio = ID3(temp_file)
        except:
            audio = ID3()

        audio['TPE1'] = TPE1(encoding=3, text=FIXED_ARTIST)
        audio['TALB'] = TALB(encoding=3, text=FIXED_ALBUM)
        audio['TIT2'] = TIT2(encoding=3, text=message.audio.title or "Music")
        
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, 'rb') as img:
                audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read())
        audio.save(v2_version=3)

        # Tugma qo'shish (Inline Button)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Kanalimizga a'zo bo'ling", url="https://t.me/freestyle_beat"))

        # Yuborish
        with open(temp_file, 'rb') as audio_file:
            thumb = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            bot.send_audio(
                chat_id, 
                audio_file,
                caption=f"✅ **Musiqa tahrirlandi!**\n\n👤 **Artist:** {FIXED_ARTIST}\n💿 **Albom:** {FIXED_ALBUM}",
                parse_mode="Markdown",
                thumb=thumb,
                performer=FIXED_ARTIST,
                reply_markup=markup
            )
            if thumb: thumb.close()

        bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ **Xatolik:** {str(e)}", chat_id, msg.message_id)
    
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

bot.polling(none_stop=True)
