import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types
from mutagen.id3 import ID3, APIC, TPE1, TALB, TIT2

# --- RENDER UCHUN KICHIK SERVER ---
app = Flask('')
@app.route('/')
def home():
    return "Bot ishlanyapti!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
# -------------------------------------

# --- SOZLAMALAR (O'zingizga moslang) ---
API_TOKEN = '8158093361:AAE4JR-rZWBNlvY_YOKxHmrOPj1rtqzqZUo'
FIXED_ARTIST = "Mening Kanalim"       
FIXED_ALBUM = "@freestyle_beat"    
IMAGE_PATH = "cover.jpg"              
# ------------------

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "<b>Xush kelibsiz!</b>\nMenga musiqa yuboring.", parse_mode="HTML")

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    chat_id = message.chat.id
    temp_file = f"music_{message.audio.file_id}.mp3"
    
    msg = bot.send_message(chat_id, "⏳ <b>Fayl tahrirlanmoqda...</b>", parse_mode="HTML")
    
    try:
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(temp_file, 'wb') as f:
            f.write(downloaded_file)

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

        # Tugma
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Kanalimizga o'ting", url="https://t.me/freestyle_beat"))

        # Yuborish (Xavfsiz HTML formatida)
        with open(temp_file, 'rb') as audio_file:
            thumb = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            bot.send_audio(
                chat_id, 
                audio_file,
                caption=f"✅ <b>Musiqa tahrirlandi!</b>\n\n👤 <b>Artist:</b> {FIXED_ARTIST}\n💿 <b>Albom:</b> {FIXED_ALBUM}",
                parse_mode="HTML",
                thumb=thumb,
                performer=FIXED_ARTIST,
                title=message.audio.title,
                reply_markup=markup
            )
            if thumb: thumb.close()

        bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.send_message(chat_id, f"Xatolik: {str(e)}")
    
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

bot.polling(none_stop=True)
