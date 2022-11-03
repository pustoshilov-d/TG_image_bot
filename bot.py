#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

import logging
from pathlib import PosixPath
import uuid
import os
import glob
import urllib.request
import random

from telegram.ext import CommandHandler, MessageHandler, Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Update


PHOTOS_DIR = "photos"
CHATS_DB = "chats.txt"
IS_PROD = bool(os.environ.get('IS_PROD', 'False'))
IS_PROD = False

APP_NAME = str(os.environ.get(
    'APP_NAME', "tg-image-bot"))
CHANCE = float(os.environ.get('CHANCE', '0.6'))
TOKEN = str(os.environ.get(
    'TOKEN', "5483400723:AAE7qPx7GVPoxIjR30YkkZuy5VaqNy1mYns"))
TOKEN = "5483400723:AAE7qPx7GVPoxIjR30YkkZuy5VaqNy1mYns"

PORT = int(os.environ.get('PORT', '8443'))

print('IS_PROD', IS_PROD)
print('TOKEN', TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    print(url)
    if str(url).startswith("http"):
        photo_path = PosixPath('photos/'+str(uuid.uuid4().fields[-1])+".jpg")

        try:
            urllib.request.urlretrieve(url, photo_path)
            await update.message.reply_photo(open(photo_path, 'rb'))
            await update.message.reply_text("Изображение принято.")
        except Exception as e:
            print('image from web is bad', e)
            await update.message.reply_text("Изображение не принято.")

    await update.message.reply_text(
        """
Чтобы сохранить изображение в базе, отправь мне его или ссылку на него, которая начинается с \"http\".
/test для единоразовой отправки во все чаты, /clear_db для очистки базы.
"""
    )


async def added(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo_file = await update.message.photo[-1].get_file()
    photo_path = PosixPath('photos/'+str(uuid.uuid4().fields[-1])+".jpg")
    await photo_file.download(photo_path)

    await update.message.reply_photo(open(photo_path, 'rb'))
    await update.message.reply_text("Изображение принято.")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


async def clear_photo_dir(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None) -> None:
    photos = glob.glob("photos/*")
    for photo in photos:
        print(photo)
        os.remove(photo)

    print('Done')
    if update:
        await update.message.reply_text("База очищена.")


async def send_photos(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None, rand=True) -> None:
    if rand and random.uniform(0, 1) > CHANCE:
        print('CHANCE falls')
        if update:
            await update.message.reply_text("Попробуй ещё раз.")
        return

    print('CHANCE wins')

    chats = open('chats.txt').readlines()
    chats = [int(chat.strip()) for chat in chats if chat != ""]
    print('chats to send', chats)

    photos = glob.glob("photos/*")
    if photos == []:
        print("no images")
        if update:
            await update.message.reply_text("Нет изображений в базе")
    chats_good = []
    for chat in chats:
        try:
            photo = random.choice(photos)
            if context:
                await context.bot.send_photo(chat, open(photo, 'rb'))
            else:
                bot = Application.builder().token(TOKEN).build().bot
                await bot.send_photo(chat, open(photo, 'rb'))

            chats_good.append(chat)
            print('chat good', chat)
        except Exception as e:
            print('chat bad', chat, e)
    if update:
        chats_good = [str(chat) for chat in chats_good]
        await update.message.reply_text(
            "Изображения отправлены в " + ", ".join(chats_good))


def main():

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("test", send_photos))
    application.add_handler(CommandHandler("clear_db", clear_photo_dir))

    application.add_handler(MessageHandler(filters.TEXT, echo))
    application.add_handler(MessageHandler(filters.PHOTO, photo))
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, added))

    application.add_error_handler(error)

    if IS_PROD:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"https://{APP_NAME}.herokuapp.com/" + TOKEN
        )
    else:
        application.run_polling()


if __name__ == '__main__':
    main()
