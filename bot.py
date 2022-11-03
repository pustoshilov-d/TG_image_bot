#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

import logging
from pathlib import PosixPath
from telegram import Update
import uuid
import os
import glob
import urllib.request
import random

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram

PHOTOS_DIR = "photos"
CHATS_DB = "chats.txt"
IS_PROD = bool(os.environ.get('IS_PROD', 'False'))
print('IS_PROD', IS_PROD)
APP_NAME = str(os.environ.get(
    'APP_NAME', "tg-image-bot"))
CHANCE = float(os.environ.get('CHANCE', '0.6'))
TOKEN = str(os.environ.get(
    'TOKEN', ""))
PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def echo(update: Filters.text, context):
    url = update.message.text
    print(url)
    if str(url).startswith("http"):
        photo_path = PosixPath('photos/'+str(uuid.uuid4().fields[-1])+".jpg")

        try:
            urllib.request.urlretrieve(url, photo_path)
            update.message.reply_photo(open(photo_path, 'rb'))
            update.message.reply_text("Изображение принято.")
        except Exception as e:
            print('image from web is bad', e)
            update.message.reply_text("Изображение не принято.")

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
        if update:
            update.message.reply_text("Попробуй ещё раз.")
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
    chats_good = []
    for chat in chats:
        try:
            photo = random.choice(photos)
            bot.send_photo(chat, open(photo, 'rb'))
            chats_good.append(chat)
            print('chat good', chat)
        except Exception as e:
            print('chat bad', chat, e)
    if update:
        chats_good = [str(chat) for chat in chats_good]
        update.message.reply_text(
            "Изображения отправлены в " + ", ".join(chats_good))


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

    if IS_PROD:
        updater.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"https://{APP_NAME}.herokuapp.com/" + TOKEN
        )
    else:
        updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
