
import config
import aspose.words as aw
import telebot
from telebot import types
from io import BytesIO
import uuid
from telebot.apihelper import download_file


bot = telebot.TeleBot(config.API_KEY)
user_images = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет, я сконвертирую любое изображение. Отправь мне фото!")

@bot.message_handler(content_types=['photo'])
def get_image_messages(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_id = str(uuid.uuid4())

    user_images[image_id] = downloaded_file

    keyboard = types.InlineKeyboardMarkup()
    for fmt in ['png', 'jpg', 'webp', 'emf', 'tiff', 'bmp']:
        keyboard.add(types.InlineKeyboardButton(text = fmt, callback_data=f'{fmt}:{image_id}'))
    bot.send_message(message.chat.id, "В какой формат конвертировать изображение?", reply_markup=keyboard)
    print(f"[DEBUG] Сохраняем image_id: {image_id}")
@bot.callback_query_handler(func=lambda call: True)
def convert_image(call):
    try:
        fmt, image_id = call.data.split(':')
        fmt = fmt.lower()
    except ValueError:
        bot.send_message(call.message.chat.id ,"Неккоректный формат кнопки")
        return


    image_data = user_images.get(image_id)

    # with open(f"debug_{fmt}_{image_id}.jpg", "wb") as f:
    #     f.write(image_data)

    if not image_data:
        bot.send_message(call.message.chat.id, "Сначала отправь изображение.")
        return

    doc = aw.Document()
    builder = aw.DocumentBuilder(doc)
    image_stream = BytesIO(image_data)
    shape = builder.insert_image(image_stream)

    output_stream = BytesIO()
    image_format = {
        "jpg": aw.SaveFormat.JPEG,
        "png": aw.SaveFormat.PNG,
        "webp": aw.SaveFormat.WEB_P,
        "tiff": aw.SaveFormat.TIFF,
        "emf": aw.SaveFormat.EMF,
        "bmp": aw.SaveFormat.BMP,
    }[fmt]


    shape.get_shape_renderer().save(output_stream, aw.saving.ImageSaveOptions(image_format))
    output_stream.seek(0)

    bot.send_document(call.message.chat.id, output_stream, visible_file_name=f'converted.{fmt}')
    bot.send_message(call.message.chat.id, "Вот твоё изображение!")
    print(f"[DEBUG] Обрабатываем callback: {fmt=} {image_id=}")
    del user_images[image_id]

bot.infinity_polling()