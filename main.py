import os
import asyncio
from aiohttp import web
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import handlers  # registers handlers on import
# ------------------ TIME-OFFSET PATCH START ------------------
# ---------------- TIME-OFFSET PATCH (multi-source) ----------------
import time as _time
import socket, struct

def _get_real_time():
    """Try several time sources and return real UTC epoch seconds."""
    # 1️⃣  Google Public NTP
    try:
        ntp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ntp.settimeout(3)
        addr = ("time.google.com", 123)
        msg = b"\x1b" + 47 * b"\0"
        ntp.sendto(msg, addr)
        data, _ = ntp.recvfrom(1024)
        if data:
            t = struct.unpack("!12I", data)[10]
            t -= 2208988800  # convert NTP to Unix
            return int(t)
    except Exception:
        pass
    # 2️⃣  Cloudflare
    try:
        ntp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ntp.settimeout(3)
        addr = ("time.cloudflare.com", 123)
        msg = b"\x1b" + 47 * b"\0"
        ntp.sendto(msg, addr)
        data, _ = ntp.recvfrom(1024)
        if data:
            t = struct.unpack("!12I", data)[10]
            t -= 2208988800
            return int(t)
    except Exception:
        pass
    # 3️⃣  WorldTimeAPI (HTTP)
    try:
        import requests as _requests
        from datetime import datetime as _dt
        r = _requests.get("https://worldtimeapi.org/api/timezone/Etc/UTC", timeout=5)
        r.raise_for_status()
        d = r.json()
        if isinstance(d.get("unixtime"), (int, float)):
            return int(d["unixtime"])
        if isinstance(d.get("datetime"), str):
            return int(_dt.fromisoformat(d["datetime"].replace("Z", "+00:00")).timestamp())
    except Exception:
        pass
    # 4️⃣  Fallback: HTTP Date header
    try:
        import requests as _requests, email.utils as eut
        r = _requests.head("https://google.com", timeout=5)
        dt = eut.parsedate_to_datetime(r.headers["Date"])
        return int(dt.timestamp())
    except Exception:
        pass
    return 0

try:
    _real = _get_real_time()
    _local = int(_time.time())
    _OFFSET = _real - _local if _real else 0
    if abs(_OFFSET) > 2:
        print(f"🕒 Time offset { _OFFSET } s — applying local patch")
        _old_time = _time.time
        _time.time = lambda: _old_time() + _OFFSET
    else:
        print(f"🕒 Time offset small ({ _OFFSET } s), no adjustment needed")
except Exception as e:
    print(f"🕒 Time patch skipped: {e}")
# ---------------- END PATCH ----------------


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
