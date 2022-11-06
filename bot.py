#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

import logging
from pathlib import PosixPath
import uuid
import os
import glob
import random
import requests

from telegram.ext import CommandHandler, MessageHandler, Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from telegram import Update


PHOTOS_DIR = "photos"
CHATS_DB = "chats.txt"
IS_PROD = bool(os.environ.get('IS_PROD', 'False'))
# IS_PROD = False
APP_NAME = str(os.environ.get(
    'APP_NAME', "tg-image-bot"))
CHANCE = float(os.environ.get('CHANCE', '0.6'))
TOKEN = str(os.environ.get('TOKEN', ""))
# TOKEN = ""
PORT = int(os.environ.get('PORT', '8443'))

print('IS_PROD', IS_PROD)
print('TOKEN', TOKEN)
print('PORT', PORT)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def get_new_image_name() -> PosixPath:
    photos = [int(os.path.basename(x).split('.')[0])
              for x in glob.glob("photos/*")]
    if photos == []:
        return PosixPath('photos/1.jpg')
    photo = PosixPath('photos/'+str(max(photos)+1)+".jpg")
    return photo


def get_first_image_name() -> PosixPath:
    photos = [int(os.path.basename(x).split('.')[0])
              for x in glob.glob("photos/*")]
    if photos == []:
        return None
    photo = PosixPath('photos/'+str(min(photos))+".jpg")
    return photo


async def register_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin = str(update.message.chat.id)
    admins = open('admins.txt', 'r').readlines()
    admins = [str(admin.strip()) for admin in admins if admin != ""]
    print('new admin', admin)
    print('admins', admins)

    if admin not in admins:
        open('admins.txt', 'a').write(admin+"\n")
        print('Admin added')
    else:
        print('Admin not added')
    await update.message.reply_text("Админ добавлен. Чтобы сохранить изображение в базе, отправь мне его. /send для во все чаты фотки в порядке стэка, /clear_db для очистки базы, /send_message отправить сообщение от имени бота во все чаты.")


def is_admin(update: Update) -> bool:
    person = str(update.message.chat.id)
    admins = open('admins.txt').readlines()
    admins = [str(admin.strip()) for admin in admins if admin != ""]

    res = person in admins
    print(person, 'is_admin', res)
    return res


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.message.reply_text("Прости, общаюсь только с админами.")
        return

    await update.message.reply_text("Чтобы сохранить изображение в базе, отправь мне его. /send для во все чаты фотки в порядке стэка, /clear_db для очистки базы, /send_message отправить сообщение от имени бота во все чаты.")


async def send_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.message.reply_text("Прости, общаюсь только с админами.")
        return

    await update.message.reply_text("Напиши сообщение:")
    return "STATE_GET_MESSAGE"


async def send_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    if not is_admin(update):
        await update.message.reply_text("Прости, общаюсь только с админами.")
        return

    await update.message.reply_text("Напиши сообщение:")
    return "STATE_GET_MESSAGE"


async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chats = open('chats.txt').readlines()
    chats = [str(chat.strip()) for chat in chats if chat != ""]
    print('chats to send', chats)

    chats_good = []
    message = update.message.text
    for chat in chats:
        try:
            if context:
                await context.bot.send_message(chat, message)
            else:
                bot = Application.builder().token(TOKEN).build().bot
                await bot.send_message(chat, message)

            chats_good.append(chat)
            print('chat good', chat)
        except Exception as e:
            print('chat bad', chat, e)

    chats_good = [str(chat) for chat in chats_good]
    await update.message.reply_text(
        "Сообщение отправлено в " + ", ".join(chats_good))
    await update.message.reply_text("Чтобы завершить отправку, нажмите /end_message")


async def send_message_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Отправка завершена.")


async def added(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    print('added')
    chat = str(update.message.chat.id)
    chats = open('chats.txt', 'r').readlines()
    chats = [str(chat.strip()) for chat in chats if chat != ""]
    print('new chat', chat)
    print('chats', chats)

    if chat not in chats:
        open('chats.txt', 'a').write(chat+"\n")
        print('Chat added')
    else:
        print('Chat not added')


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.message.reply_text("Прости, общаюсь только с админами.")
        return

    photo_file = await update.message.photo[-1].get_file()
    photo_path = get_new_image_name()
    print(photo_path)
    await photo_file.download(photo_path)

    await update.message.reply_photo(open(photo_path, 'rb'))
    await update.message.reply_text("Изображение принято.")
    print('Изображение принято. База:', glob.glob("photos/*"))


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


async def clear_photo_dir(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None) -> None:
    if not is_admin(update):
        await update.message.reply_text("Прости, общаюсь только с админами.")
        return
    photos = glob.glob("photos/*")
    for photo in photos:
        print(photo)
        os.remove(photo)

    print('Done')
    await update.message.reply_text("База очищена.")


async def send_photos(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None, rand=True) -> None:
    if not is_admin(update):
        await update.message.reply_text("Прости, общаюсь только с админами.")
        return
    # if rand and random.uniform(0, 1) > CHANCE:
    #     print('CHANCE falls')
    #     if update:
    #         await update.message.reply_text("Попробуй ещё раз.")
    #     return

    # print('CHANCE wins')

    chats = open('chats.txt').readlines()
    chats = [str(chat.strip()) for chat in chats if chat != ""]
    print('chats to send', chats)

    photo = get_first_image_name()

    if photo == None:
        print("no images")
        if update:
            await update.message.reply_text("Нет изображений в базе, добавьте!")
        return

    chats_good = []
    for chat in chats:
        try:
            # photo = random.choice(photos)
            if context:
                await context.bot.send_photo(chat, open(photo, 'rb'))
            else:
                bot = Application.builder().token(TOKEN).build().bot
                await bot.send_photo(chat, open(photo, 'rb'))

            chats_good.append(chat)
            print('chat good', chat)
        except Exception as e:
            print('chat bad', chat, e)

    chats_good = [str(chat) for chat in chats_good]
    await update.message.reply_text(
        "Изображения отправлены в " + ", ".join(chats_good))
    os.remove(photo)


def main():

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("make_me_admin", register_admin))
    application.add_handler(CommandHandler("send", send_photos))
    application.add_handler(CommandHandler("clear_db", clear_photo_dir))

    # application.add_handler(CommandHandler("send_message", send_message))
    # application.add_handler(MessageHandler(filters.TEXT, echo))

    application.add_handler(MessageHandler(filters.PHOTO, photo))
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, added))

    application.add_handler(MessageHandler(filters.TEXT, start))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("send_message", send_message_command)],
        states={
            "STATE_GET_MESSAGE": [
                MessageHandler(filters.TEXT, send_message)
            ],
        },
        fallbacks=[CommandHandler("end_message", send_message_done)],
    )
    application.add_handler(conv_handler)

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
