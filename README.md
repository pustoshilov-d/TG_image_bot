`pipenv run python bot.py`


python clear_db.py
`pipenv run python -c 'import bot; import asyncio;  print(asyncio.run(bot.clear_photo_dir()))'`

python send_photos.py
`python -c 'import bot; import asyncio;  print(asyncio.run(bot.send_photos()))''`