import os
import glob
import asyncio


async def clear_photo_dir(update=None, context=None) -> None:
    photos = glob.glob("photos/*")
    for photo in photos:
        print(photo)
        os.remove(photo)
    print('Done')

if __name__ == '__main__':
    asyncio.run(clear_photo_dir())
