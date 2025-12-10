import os
import asyncio
from aiohttp import web
from pyrogram import Client
from bot.config import API_ID, API_HASH, BOT_TOKEN
from bot import handlers  # registers handlers on import

# ---------------- TIME-OFFSET PATCH (multi-source + forced forward) ----------------
import time as _time
import socket
import struct

def _get_real_time():
    """Try multiple sources to obtain current UTC unix time."""
    # 1) Google NTP (UDP)
    try:
        ntp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ntp.settimeout(3)
        addr = ("time.google.com", 123)
        msg = b"\x1b" + 47 * b"\0"
        ntp.sendto(msg, addr)
        data, _ = ntp.recvfrom(1024)
        if data:
            t = struct.unpack("!12I", data)[10]
            t -= 2208988800
            ntp.close()
            return int(t)
    except Exception:
        pass

    # 2) Cloudflare NTP (UDP)
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
            ntp.close()
            return int(t)
    except Exception:
        pass

    # 3) HTTP Date header fallback (robust, low-rate-limit risk)
    try:
        import requests as _requests
        import email.utils as _eut
        r = _requests.head("https://google.com", timeout=5)
        if "Date" in r.headers:
            dt = _eut.parsedate_to_datetime(r.headers["Date"])
            return int(dt.timestamp())
    except Exception:
        pass

    return 0

try:
    _real = _get_real_time()
    _local = int(_time.time())
    _OFFSET = _real - _local if _real else 0

    # If offset is too small (or real-time fetch failed), force a small forward drift
    # so msg_id won't be too low even if the container clock lags.
    if abs(_OFFSET) <= 2:
        _OFFSET = 10
        print(f"🕒 Time offset small or unavailable; forcing +{_OFFSET}s forward drift (container may be slow).")
    else:
        print(f"🕒 Applying process time() offset: {_OFFSET}s (real={_real}, local={_local})")

    _old_time = _time.time
    _time.time = lambda: _old_time() + _OFFSET

except Exception as e:
    print(f"🕒 Time patch skipped due to error: {e}")
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
    try:
        await asyncio.gather(
            app.start(),
            run_http_server()
        )
        print("🤖 Bot started and running...")
        await app.idle()
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
