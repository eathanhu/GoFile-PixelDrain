import os
import asyncio
from aiohttp import web
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import handlers  # registers handlers on import

# Telegram client
app = Client("gofile_pixeldrain_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Simple health check for Render
async def health_check(request):
    return web.Response(text="Bot is running fine!")

async def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = web.Application()
    server.add_routes([web.get("/", health_check)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Health check listening on port {port}")

async def main():
    await asyncio.gather(
        app.start(),
        run_http_server()
    )
    print("🤖 Bot started and running...")
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
