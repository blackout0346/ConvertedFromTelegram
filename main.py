import config
from PIL import Image
import telebot
from telebot import types
from io import BytesIO
import uuid
import os
from pydub import AudioSegment
import speech_recognition as sr
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(BASE_DIR, 'ffmpeg')


bot = telebot.TeleBot(config.API_KEY)
user_images = {}
user_media = {}
user_mode ={}

@bot.message_handler(commands=['start','mode','image','audio', 'voice'])
def start_message(message):
    keyboard_quest = types.InlineKeyboardMarkup()

    keyboard_quest.add(types.InlineKeyboardButton(text ='Конвертировать изображения', callback_data='mode:image'))
    keyboard_quest.add(types.InlineKeyboardButton(text='Конвертировать аудио', callback_data='mode:audio'))
    keyboard_quest.add(types.InlineKeyboardButton(text='Преобразовать гс в текст', callback_data='mode:voice'))
    bot.send_message(message.chat.id, "Привет, я конвёртер и могу сконвертировать изображения, аудио и голосовые сообщения! Выбери режим",reply_markup=keyboard_quest)



@bot.callback_query_handler(func = lambda call: call.data.startswith('mode:'))
def set_quest(call):
    mode = call.data.split(':')[1]
    user_id= call.message.chat.id
    user_mode[user_id] = mode

    if mode == 'image':
        bot.send_message(call.message.chat.id, "режим конвертации фото")
        return

    elif mode == 'audio':
        bot.send_message(call.message.chat.id, "режим конвертации аудио")
        return
    elif mode == 'voice':
        bot.send_message(call.message.chat.id, "режим конвертации гс в текст")
        return


@bot.message_handler(content_types=['voice'])
def get_voice_message(message):
    user_id = message.chat.id
    if user_mode.get(user_id) !='voice':
        bot.send_message(message.chat.id, "Выберите voice")
        return
    try:
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        download_file = bot.download_file(file_info.file_path)
        user_media[user_id] = download_file
        media_id = str(uuid.uuid4())
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(

            text="Распознать текст", callback_data=f"voice:{media_id}"
        ))

        bot.send_message(message.chat.id, "Голосовое получено, нажмите для распознавания:", reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка получения гс:{e}')
@bot.callback_query_handler(func=lambda call:call.data.startswith('voice',command='voice'))
def convert_voice_to_text(call):
    try:
        _, media_id = call.data.split(':', 1)
    except ValueError:
        bot.send_message(call.message.chat.id, "Некорректный формат кнопки")
        return
    voice_id =call.message.chat.id
    voice_stream = user_media.get(voice_id)
    if not voice_stream:
        bot.send_message(call.message.chat.id, "Отправь гс")
        return
    try:

        audio = AudioSegment.from_file(BytesIO(voice_stream), format='ogg')
        wav_io = BytesIO()
        audio.export(wav_io, format='wav')
        wav_io.seek(0)

        record = sr.Recognizer()

        with sr.AudioFile(wav_io) as source:
            audio_data = record.record(source)
        text_record = record.recognize_google(audio_data,language='ru-RU')
        bot.send_message(call.message.chat.id,f'{text_record}')
        del user_media[voice_id]

    except Exception as e:
        bot.send_message(call.message.chat.id, f'Ошибка в конвертации{e}')
@bot.message_handler(content_types=['audio', 'video'])
def get_audio_message(message):
    user_id = message.chat.id
    if user_mode.get(user_id) != 'audio':
        bot.send_message(message.chat.id, "Выберите audio")
        return
    try:
        if message.content_type == 'audio':
            file_id = message.audio.file_id
            file_name = message.audio.file_name or'audio.file'

        else:
            file_id = message.video.file_id
            file_name = message.video.file_name or'video.file'

        file_info = bot.get_file(file_id)
        download_file = bot.download_file(file_info.file_path)
        media_id = str(uuid.uuid4())
        user_media[media_id] = {
            'data': download_file,
            'original_name': file_name
        }

        keyboard = types.InlineKeyboardMarkup()
        for fmt in ['mp3','wav','ogg']:
            keyboard.add(types.InlineKeyboardButton(text=fmt, callback_data=f'audio:{fmt}:{media_id}'))
        bot.send_message(message.chat.id, "В каком формате конвертировать?",reply_markup=keyboard)
        print(f"[DEBUG] Сохраняем video_id: {media_id}")
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка при загрузке файла.{str(e)}')

@bot.message_handler(content_types=['photo'])
def get_image_messages(message):
    user_id = message.chat.id
    if user_mode.get(user_id) != 'image':
        bot.send_message(message.chat.id,"Выбери режим image")
        return

    file_info = bot.get_file(message.photo[-1].file_id)

    downloaded_file = bot.download_file(file_info.file_path)

    image_id = str(uuid.uuid4())

    user_images[image_id] = downloaded_file

    keyboard = types.InlineKeyboardMarkup()
    for fmt in ['png', 'jpeg', 'webp', 'pdf','ico','tga','ppm', 'tiff', 'bmp']:
        keyboard.add(types.InlineKeyboardButton(text = fmt, callback_data=f'image:{fmt}:{image_id}'))
    bot.send_message(message.chat.id, "В каком формат конвертировать изображение?", reply_markup=keyboard)


    print(f"[DEBUG] Сохраняем image_id: {image_id}")
@bot.callback_query_handler(func=lambda call: call.data.startswith('audio:'))
def convert_audio(call):
    try:
        audio, fmt, media_id = call.data.split(':')
        fmt = fmt.lower()
    except ValueError:
        bot.send_message(call.message.chat.id, "Неккоректный формат кнопки")
        return
    media_info = user_media.get(media_id)

    if not media_info:
        bot.send_message(call.message.chat.id, "Сначала отправь видео или аудио.")
        return

    try:
        bot.send_message(call.message.chat.id, "Конвертирую...")

        audio_data = BytesIO(media_info['data'])
        original_name = media_info['original_name']

        audio_data.seek(0)
        sound = AudioSegment.from_file(audio_data)

        output_stream = BytesIO()
        sound.export(output_stream, format=fmt)
        output_stream.seek(0)

        output_name = f'{os.path.splitext(original_name)[0]}.{fmt}'
        bot.send_document(call.message.chat.id, output_stream, visible_file_name=output_name)

        del user_media[media_id]
        print(f"[DEBUG] Обрабатываем callback: {fmt=} {media_id=}")
    except Exception as e:
        bot.send_message(call.message.chat.id, f'Ошибка в конвертации.{str(e)}')


@bot.callback_query_handler(func=lambda call: call.data.startswith('image'))
def convert_image(call):
    try:
        image, fmt, image_id = call.data.split(':')
        fmt = fmt.lower()
    except ValueError:
        bot.send_message(call.message.chat.id ,"Неккоректный формат кнопки")
        return


    image_data = user_images.get(image_id)

    if not image_data:
        bot.send_message(call.message.chat.id, "Сначала отправь изображение.")
        return
    image_stream = BytesIO(image_data)
    img = Image.open(image_stream).convert("RGB")
    output_stream = BytesIO()

    img.save(output_stream , format=fmt.upper())
    output_stream.seek(0)
    bot.send_document(call.message.chat.id, output_stream , visible_file_name=f"converted.{fmt}")
    bot.send_message(call.message.chat.id, "Вот твоё изображение!")

    print(f"[DEBUG] Обрабатываем callback: {fmt=} {image_id=}")
    del user_images[image_id]

bot.infinity_polling()