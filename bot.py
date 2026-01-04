import os
import telebot
import yt_dlp
from telebot import types
from flask import Flask
from threading import Thread
from mutagen.id3 import ID3, APIC, TPE1, TALB, TIT2
from mutagen.mp4 import MP4, MP4Cover
from mutagen import File as MutagenFile

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Live!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()

# --- SOZLAMALAR ---
API_TOKEN = '8158093361:AAELuYvWD7CqucE9GxkYILbgBPk3AqNnzmo'
FIXED_ARTIST = "Subscribe"
FIXED_ALBUM = "@freestyle_beat"
IMAGE_PATH = "cover.jpg"

bot = telebot.TeleBot(API_TOKEN)

# --- TAHRIRLASH ---
def edit_audio(file_path, title, ext):
    try:
        if ext == ".mp3":
            try: audio = ID3(file_path)
            except: audio = ID3()
            audio['TPE1'] = TPE1(encoding=3, text=FIXED_ARTIST)
            audio['TALB'] = TALB(encoding=3, text=FIXED_ALBUM)
            audio['TIT2'] = TIT2(encoding=3, text=title)
            if os.path.exists(IMAGE_PATH):
                with open(IMAGE_PATH, 'rb') as img:
                    audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read())
            audio.save(v2_version=3)
        elif ext == ".m4a":
            audio = MP4(file_path)
            audio["\xa9ART"] = FIXED_ARTIST
            audio["\xa9alb"] = FIXED_ALBUM
            audio["\xa9nam"] = title
            if os.path.exists(IMAGE_PATH):
                with open(IMAGE_PATH, "rb") as img:
                    audio["covr"] = [MP4Cover(img.read(), imageformat=MP4Cover.FORMAT_JPEG)]
            audio.save()
    except: pass

# --- YOUTUBE YUKLOVCHI (XAVFSIZ VARIANT) ---
def download_yt(url, chat_id):
    file_name = f"yt_{chat_id}"
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best', # Eng barqaror format
        'outtmpl': f'{file_name}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', # Bot emasligini ko'rsatish
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        ext = os.path.splitext(file_path)[1]
        return file_path, info.get('title', 'YouTube Music'), int(info.get('duration', 0)), ext

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "<b>Tayyorman!</b>\nLink yuboring yoki fayl tashlang.", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and ('youtube.com' in m.text or 'youtu.be' in m.text))
def handle_youtube(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "📥 <b>Yuklanmoqda...</b>", parse_mode="HTML")
    try:
        file_path, title, duration, ext = download_yt(message.text, chat_id)
        edit_audio(file_path, title, ext)
        
        with open(file_path, 'rb') as f:
            thumb = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            bot.send_audio(chat_id, f, caption=f"⚡ <b>New:</b> {FIXED_ARTIST}\n💿 <b>Albom:</b> {FIXED_ALBUM}", 
                           parse_mode="HTML", thumb=thumb, performer=FIXED_ARTIST, title=title, duration=duration)
            if thumb: thumb.close()
        bot.delete_message(chat_id, msg.message_id)
        if os.path.exists(file_path): os.remove(file_path)
    except Exception as e:
        bot.edit_message_text(f"❌ YouTube blokladi yoki xatolik. Keyinroq urunib ko'ring.", chat_id, msg.message_id)

@bot.message_handler(content_types=['audio', 'document'])
def handle_audio(message):
    # Oldingi ishlayotgan tahrirlash kodingizni bu yerga qo'shishingiz mumkin
    # Yoki yuqoridagi edit_audio funksiyasidan foydalaning
    pass

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
