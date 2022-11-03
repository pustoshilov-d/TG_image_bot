#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

import logging
from pathlib import PosixPath
from telegram import Update
import uuid
import requests
import os
import glob
import random

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ContextTypes
import telegram

PHOTOS_DIR = "photos"
CHATS_DB = "chats.txt"
APP_NAME = str(os.environ.get('APP_NAME', "https://tg-image-bot.herokuapp.com/"))
CHANCE = float(os.environ.get('CHANCE', '0.6'))
TOKEN = str(os.environ.get('TOKEN', "5483400723:AAEsfZkClxYZWyfVf8UO_Z5-xQI2y2J9IyE"))
PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def echo(update: Filters.text, context):
    url = update.message.text
    if str(url).startswith("http"):
        photo_path = PosixPath('photos/'+str(uuid.uuid4().fields[-1])+".jpg")

        img_data = requests.get(url).content
        with open(photo_path, 'wb') as handler:
            handler.write(img_data)
        # update.message.reply_photo(open(photo_path, 'rb'))
        update.message.reply_text("Изображение принято.")

    update.message.reply_text(
        """
Чтобы сохранить изображение в базе, отправь мне его или ссылку на него, которая начинается с \"http\".
/test для единоразовой отправки во все чаты, /clear_db для очистки базы.
"""
    )


def added(update: Filters.status_update.new_chat_members, context):
    """Echo the user message."""
    print('added')
    chat = str(update.message.chat.id)
    chats = open('chats.txt', 'r').readlines()
    chats = [chat.strip() for chat in chats if chat != ""]
    print('new chat', chat)
    print('chats', chats)

    if chat not in chats:
        open('chats.txt', 'a').write(chat+"\n")
        print('Added')
    else:
        print('Not added')


def photo(update: Update, context):
    """Stores the photo and asks for a location."""
    user = update.message.from_user

    photo_file = update.message.photo[-1].get_file()
    photo_path = PosixPath('photos/'+str(uuid.uuid4().fields[-1])+".jpg")
    photo_file.download(photo_path)

    update.message.reply_photo(open(photo_path, 'rb'))
    update.message.reply_text("Изображение принято.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def clear_photo_dir(update=None, context=None):
    photos = glob.glob("photos/*")
    for photo in photos:
        print(photo)
        os.remove(photo)

    print('Done')
    if update:
        update.message.reply_text("База очищена.")


def send_photos(update=None, context=None, rand=True):
    if rand and random.uniform(0, 1) > CHANCE:
        print('CHANCE falls')
        return

    print('CHANCE wins')
    bot = telegram.Bot(token=TOKEN)

    chats = open('chats.txt').readlines()
    chats = [int(chat.strip()) for chat in chats if chat != ""]
    print('chats to send', chats)

    photos = glob.glob("photos/*")
    if photos == []:
        print("no images")
        if update:
            update.message.reply_text("Нет изображений в базе")
    for chat in chats:
        try:
            photo = random.choice(photos)
            bot.send_photo(chat, open(photo, 'rb'))
            print('chat good', chat)
        except Exception as e:
            print('chat bad', chat, e)
    if update:
        update.message.reply_text(
            "Изображения отправлены в", ", ".join(chats))


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("test", send_photos))
    dp.add_handler(CommandHandler("clear_db", clear_photo_dir))

    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_handler(MessageHandler(Filters.photo, photo))
    dp.add_handler(MessageHandler(
        Filters.status_update.new_chat_members, added))

    dp.add_error_handler(error)

    # updater.start_polling()

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN)
    # updater.bot.set_webhook(url=settings.WEBHOOK_URL)
    updater.bot.set_webhook(APP_NAME + TOKEN)

    updater.idle()


if __name__ == '__main__':
    main()
