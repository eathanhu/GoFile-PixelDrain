from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import handlers  # registers handlers on import


def run():
    app = Client('gofile_pixeldrain_bot', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    app.run()


if __name__ == '__main__':
    run()
