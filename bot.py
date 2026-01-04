import os
import telebot
import yt_dlp
from telebot import types
from flask import Flask
from threading import Thread
from mutagen.id3 import ID3, APIC, TPE1, TALB, TIT2
from mutagen.mp4 import MP4, MP4Cover
from mutagen import File as MutagenFile

# --- RENDER UCHUN SERVER ---
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

# --- TAHRIRLASH FUNKSIYALARI ---
def edit_mp3(file_path, title):
    try:
        try: audio = ID3(file_path)
        except: audio = ID3()
        audio['TPE1'] = TPE1(encoding=3, text=FIXED_ARTIST)
        audio['TALB'] = TALB(encoding=3, text=FIXED_ALBUM)
        audio['TIT2'] = TIT2(encoding=3, text=title)
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, 'rb') as img:
                audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read())
        audio.save(v2_version=3)
    except: pass

def edit_m4a(file_path, title):
    try:
        audio = MP4(file_path)
        audio["\xa9ART"] = FIXED_ARTIST
        audio["\xa9alb"] = FIXED_ALBUM
        audio["\xa9nam"] = title
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, "rb") as img:
                audio["covr"] = [MP4Cover(img.read(), imageformat=MP4Cover.FORMAT_JPEG)]
        audio.save()
    except: pass

def download_yt(url, chat_id):
    file_name = f"yt_{chat_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': file_name + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return file_name + ".mp3", info.get('title', 'YouTube Music'), int(info.get('duration', 0))

# --- HANDLERLAR ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "<b>Tayyorman!</b>\n\nYouTube link yuboring yoki musiqa fayli tashlang.", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and ('youtube.com' in m.text or 'youtu.be' in m.text))
def handle_youtube(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "📥 <b>YouTube'dan yuklanmoqda...</b>", parse_mode="HTML")
    try:
        file_path, title, duration = download_yt(message.text, chat_id)
        edit_mp3(file_path, title)
        with open(file_path, 'rb') as audio_file:
            thumb = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            bot.send_audio(chat_id, audio_file, caption=f"⚡ <b>New:</b> {FIXED_ARTIST}\n💿 <b>Albom:</b> {FIXED_ALBUM}", parse_mode="HTML", thumb=thumb, performer=FIXED_ARTIST, title=title, duration=duration)
            if thumb: thumb.close()
        bot.delete_message(chat_id, msg.message_id)
        if os.path.exists(file_path): os.remove(file_path)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi. Linkni tekshiring.", chat_id, msg.message_id)

@bot.message_handler(content_types=['audio', 'document'])
def handle_audio(message):
    file_id = None
    file_name = ""
    orig_duration = 0
    if message.content_type == 'audio':
        file_id = message.audio.file_id
        file_name = message.audio.title or "music"
        orig_duration = message.audio.duration
    elif message.content_type == 'document' and message.document.mime_type in ['audio/mp4', 'audio/mpeg', 'audio/x-m4a']:
        file_id = message.document.file_id
        file_name = message.document.file_name

    if not file_id: return
    chat_id = message.chat.id
    ext = ".m4a" if "m4a" in file_name.lower() else ".mp3"
    temp_file = f"music_{chat_id}{ext}"
    msg = bot.send_message(chat_id, "⏳ <b>Tahrirlanmoqda...</b>", parse_mode="HTML")
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(temp_file, 'wb') as f: f.write(downloaded_file)
        if ext == ".m4a": edit_m4a(temp_file, file_name)
        else: edit_mp3(temp_file, file_name)
        audio_info = MutagenFile(temp_file)
        duration = int(audio_info.info.length) if audio_info else orig_duration
        with open(temp_file, 'rb') as audio_file:
            thumb = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            bot.send_audio(chat_id, audio_file, caption=f"⚡ <b>New:</b> {FIXED_ARTIST}\n💿 <b>Albom:</b> {FIXED_ALBUM}", parse_mode="HTML", thumb=thumb, performer=FIXED_ARTIST, title=file_name, duration=duration)
            if thumb: thumb.close()
        bot.delete_message(chat_id, msg.message_id)
    except: bot.send_message(chat_id, "❌ Xatolik.")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
            
