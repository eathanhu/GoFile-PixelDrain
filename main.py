import os
import asyncio
from aiohttp import web
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import handlers  # registers handlers on import
# ------------------ TIME-OFFSET PATCH START ------------------
import time as _time

def _apply_process_time_offset(print_log=True):
    """Fetch UTC from worldtimeapi and apply a process-local offset to time.time()
    if the host/container clock is off and the process cannot set system time.
    This does NOT change the OS clock; it only adjusts Python's time.time() return.
    """
    try:
        import requests as _requests
        from datetime import datetime as _dt
    except Exception as e:
        if print_log:
            print(f"Time-offset: 'requests' not available, skipping time-sync: {e}")
        return

    try:
        r = _requests.get("https://worldtimeapi.org/api/timezone/Etc/UTC", timeout=5)
        r.raise_for_status()
        d = r.json()
        if isinstance(d.get("unixtime"), (int, float)):
            real = int(d["unixtime"])
        else:
            dt_s = d.get("datetime")
            if dt_s:
                try:
                    real = int(_dt.fromisoformat(dt_s.replace("Z", "+00:00")).timestamp())
                except Exception:
                    real = 0
            else:
                real = 0
    except Exception as e:
        if print_log:
            print(f"Time-offset: worldtime fetch failed: {e}")
        return

    try:
        local = int(_time.time())
        offset = real - local
    except Exception as e:
        if print_log:
            print(f"Time-offset: failed to compute offset: {e}")
        return

    # Apply only when offset is significant (>2s)
    if abs(offset) > 2:
        if print_log:
            print(f"Time-offset: applying process offset {offset}s (real={real}, local={local})")
        _old_time = _time.time
        _time.time = lambda: _old_time() + offset
    else:
        if print_log:
            print(f"Time-offset: offset small ({offset}s). No adjustment needed.")

# Run the time-offset check now so it is in effect before creating the Pyrogram client
_apply_process_time_offset()
# ------------------ TIME-OFFSET PATCH END ------------------


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
