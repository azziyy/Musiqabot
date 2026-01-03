import os
import telebot
from mutagen.id3 import ID3, APIC, TPE1, TALB, TIT2

# --- SOZLAMALAR ---
API_TOKEN = '8158093361:AAE4JR-rZWBNlvY_YOKxHmrOPj1rtqzqZUo'
FIXED_ARTIST = "Mening Kanalim"       # Artist qismiga yoziladigan nom
FIXED_ALBUM = "@kanalingiz_linki"    # Albom qismiga yoziladigan nom
IMAGE_PATH = "cover.jpg"              # GitHub'ga yuklangan rasm nomi
# ------------------

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Menga musiqa (mp3) yuboring, men uni kanalingiz nomiga moslab tahrirlab beraman. 🎵")

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    chat_id = message.chat.id
    # Vaqtinchalik fayl nomlari
    temp_music = f"music_{chat_id}.mp3"
    
    try:
        status_msg = bot.send_message(chat_id, "⏳ Jarayon bajarilmoqda...")

        # 1. Faylni yuklab olish
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(temp_music, 'wb') as f:
            f.write(downloaded_file)

        # 2. Metadatalarni (Teglarni) o'zgartirish
        try:
            audio = ID3(temp_music)
        except:
            audio = ID3()

        # Artist, Albom va Qo'shiq nomi
        audio['TPE1'] = TPE1(encoding=3, text=FIXED_ARTIST)
        audio['TALB'] = TALB(encoding=3, text=FIXED_ALBUM)
        audio['TIT2'] = TIT2(encoding=3, text=message.audio.title or "Music")
        
        # Musiqa ichiga rasmini joylash
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

        # 3. Tayyor faylni yuborish
        with open(temp_music, 'rb') as music_file:
            # Thumbnail (kichik rasm) ko'rinishi uchun
            thumb_file = open(IMAGE_PATH, 'rb') if os.path.exists(IMAGE_PATH) else None
            
            bot.send_audio(
                chat_id, 
                music_file, 
                caption=f"✅ <b>Tahrirlandi:</b> {FIXED_ARTIST}\n@sizning_kanalingiz",
                parse_mode="HTML",
                thumb=thumb_file, # Rasm tepadagi kichik holatda chiqishi uchun
                performer=FIXED_ARTIST,
                title=message.audio.title
            )
            
            if thumb_file: thumb_file.close()

        # 4. Tozalash (Serverdan faylni o'chirish)
        bot.delete_message(chat_id, status_msg.message_id)
        if os.path.exists(temp_music):
            os.remove(temp_music)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Xatolik yuz berdi: {e}")
        if os.path.exists(temp_music):
            os.remove(temp_music)

print("Bot ishga tushdi...")
bot.polling(none_stop=True)
