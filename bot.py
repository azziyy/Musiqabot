import os
import telebot
from mutagen.id3 import ID3, APIC, TPE1, TALB, TIT2

# MA'LUMOTLAR
API_TOKEN = '8158093361:AAE4JR-rZWBNlvY_YOKxHmrOPj1rtqzqZUo'
FIXED_ARTIST = "Mening Kanalim"  # Bu yerga kanal nomingizni yozing
FIXED_ALBUM = "@kanalingiz_linki" 
IMAGE_PATH = "cover.jpg" # Rasm nomi

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    try:
        chat_id = message.chat.id
        msg = bot.send_message(chat_id, "Fayl yuklanmoqda va tahrirlanmoqda...")

        # Faylni yuklab olish
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = "music.mp3"
        with open(file_name, 'wb') as f:
            f.write(downloaded_file)

        # Metadatalarni o'zgartirish
        try:
            audio = ID3(file_name)
        except:
            audio = ID3()

        audio['TPE1'] = TPE1(encoding=3, text=FIXED_ARTIST)
        audio['TALB'] = TALB(encoding=3, text=FIXED_ALBUM)
        audio['TIT2'] = TIT2(encoding=3, text=message.audio.title or "Music")
        
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, 'rb') as img:
                audio['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read())
        
        audio.save(v2_version=3)

        # Yuborish
        with open(file_name, 'rb') as music:
            bot.send_audio(chat_id, music, caption=f"✅ Tahrirlandi: {FIXED_ARTIST}")
        
        bot.delete_message(chat_id, msg.message_id)
        os.remove(file_name)

    except Exception as e:
        bot.send_message(chat_id, f"Xato: {e}")

bot.polling()
