import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types
from mutagen.id3 import ID3, APIC, TPE1, TALB, TIT2

# --- RENDER PORT XATOSINI TUZATISH VA CRON-JOB UCHUN KICHIK SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run():
    # Render avtomatik beradigan PORT ni oladi, bo'lmasa 8080 ni ishlatadi
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Botni uyg'oq saqlash xizmatini ishga tushirish
keep_alive()
# ---------------------------------------------------------------------

# --- SOZLAMALAR ---
# DIQQAT: Token yangilangan bo'lsa, @BotFather'dan olgan oxirgi tokenni qo'ying
API_TOKEN = '8158093361:AAELuYvWD7CqucE9GxkYILbgBPk3AqNnzmo'
FIXED_ARTIST = "Subscribe"       
FIXED_ALBUM = "@freestyle_beat"    
IMAGE_PATH = "cover.jpg"              
# ------------------

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "<b>Salom! Musiqa tahrirlash botiga xush kelibsiz.</b>\n\nMenga .mp3 fayl yuboring, men uni kanalingiz nomiga moslab tahrirlab beraman. 🎵", 
        parse_mode="HTML"
    )

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    chat_id = message.chat.id
    temp_file = f"music_{chat_id}_{message.audio.file_id}.mp3"
    
    msg = bot.send_message(chat_id, "⏳ <b>Fayl qayta ishlanmoqda...</b>", parse_mode="HTML")
    
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
                audio['APIC'] = APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=img.read()
                )
        
        audio.save(v2_version=3)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Kanalimizga a'zo bo'ling", url="https://t.me/freestyle_beat"))

        with open(temp_file, 'rb') as audio_file:
            thumb = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            
            bot.send_audio(
                chat_id, 
                audio_file,
                caption=f"⚡ <b>New:</b> {FIXED_ARTIST}\n💿 <b>Albom:</b> {FIXED_ALBUM}",
                parse_mode="HTML",
                thumb=thumb,
                performer=FIXED_ARTIST,
                title=message.audio.title,
                reply_markup=markup
            )
            
            if thumb: thumb.close()

        bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.send_message(chat_id, f"❌ <b>Xatolik:</b>\n<code>{str(e)}</code>", parse_mode="HTML")
    
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# --- CONFLICT 409 XATOSINI TUZATUVCHI QISM ---
if __name__ == "__main__":
    print("Bot ulanmoqda...")
    try:
        # Eski barcha ulanishlarni o'chirib tashlash
        bot.remove_webhook()
        # Botni cheksiz ulanishda ishga tushirish
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        
