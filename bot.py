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
API_TOKEN = '8158093361:AAE4JR-rZWBNlvY_YOKxHmrOPj1rtqzqZUo'
FIXED_ARTIST = "Mening Kanalim"       # Musiqaning artist qismiga yoziladigan nom
FIXED_ALBUM = "@freestyle_beat"      # Albom qismiga yoziladigan nom
IMAGE_PATH = "cover.jpg"              # GitHub'dagi rasm nomi
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
    # Har bir foydalanuvchi uchun alohida fayl nomi yaratamiz
    temp_file = f"music_{chat_id}_{message.audio.file_id}.mp3"
    
    msg = bot.send_message(chat_id, "⏳ <b>Fayl qayta ishlanmoqda...</b>", parse_mode="HTML")
    
    try:
        # 1. Faylni Telegram serveridan yuklab olish
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(temp_file, 'wb') as f:
            f.write(downloaded_file)

        # 2. Metadatalarni (Teglarni) o'zgartirish
        try:
            audio = ID3(temp_file)
        except:
            audio = ID3()

        # Artist, Albom va Qo'shiq nomi (HTML xatolarisiz)
        audio['TPE1'] = TPE1(encoding=3, text=FIXED_ARTIST)
        audio['TALB'] = TALB(encoding=3, text=FIXED_ALBUM)
        audio['TIT2'] = TIT2(encoding=3, text=message.audio.title or "Music")
        
        # Musiqa ichiga rasmni joylash
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

        # 3. Inline Tugma (Kanalga havola)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Kanalga a'zo bo'ling", url="https://t.me/freestyle_beat"))

        # 4. Tayyor faylni yuborish
        with open(temp_file, 'rb') as audio_file:
            # Thumbnail (kichik rasm) ko'rinishi uchun rasm faylini ochamiz
            thumb = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            
            bot.send_audio(
                chat_id, 
                audio_file,
                caption=f"⚡ <b>New</b> {FIXED_ARTIST}\n💿 <b>Albom:</b> {FIXED_ALBUM}",
                parse_mode="HTML",
                thumb=thumb,
                performer=FIXED_ARTIST,
                title=message.audio.title,
                reply_markup=markup
            )
            
            if thumb: thumb.close()

        # Jarayon tugagach xabarni o'chirish
        bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.send_message(chat_id, f"❌ <b>Xatolik yuz berdi:</b>\n<code>{str(e)}</code>", parse_mode="HTML")
    
    finally:
        # Server xotirasini tozalash (Faylni o'chirish)
        if os.path.exists(temp_file):
            os.remove(temp_file)

# Botni doimiy ulanishda ushlab turish
if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
