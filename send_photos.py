import os
import glob
import random
from telegram.ext import Application
import asyncio

CHANCE = float(os.environ.get('CHANCE', '0.6'))
TOKEN = str(os.environ.get('TOKEN', ""))
# TOKEN = ""


async def send_photos(update=None, context=None, rand=True) -> None:
    if rand and random.uniform(0, 1) > CHANCE:
        print('CHANCE falls')
        print("Попробуй ещё раз.")
        return

    print('CHANCE wins')

    chats = open('chats.txt').readlines()
    chats = [int(chat.strip()) for chat in chats if chat != ""]
    print('chats to send', chats)

    photos = glob.glob("photos/*")
    if photos == []:
        print("Нет изображений в базе")

    chats_good = []
    for chat in chats:
        try:
            photo = random.choice(photos)
            bot = Application.builder().token(TOKEN).build().bot
            await bot.send_photo(chat, open(photo, 'rb'))

            chats_good.append(chat)
            print('chat good', chat)
        except Exception as e:
            print('chat bad', chat, e)

    chats_good = [str(chat) for chat in chats_good]
    print("Изображения отправлены в " + ", ".join(chats_good))


if __name__ == '__main__':
    asyncio.run(send_photos())
