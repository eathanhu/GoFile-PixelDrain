import os
import asyncio
from aiohttp import web
from pyrogram import Client
from bot.config import API_ID, API_HASH, BOT_TOKEN
from bot import handlers  # registers handlers on import

# ---------------- IMPROVED TIME-OFFSET PATCH ----------------
import time as _time
import socket
import struct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_ntp_time(host: str, port: int = 123, timeout: int = 3) -> int:
    """Get time from NTP server."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(timeout)
        
        # NTP request packet (version 3, client mode)
        ntp_packet = b'\x1b' + 47 * b'\x00'
        client.sendto(ntp_packet, (host, port))
        
        data, _ = client.recvfrom(1024)
        if len(data) >= 48:
            # Extract transmit timestamp (bytes 40-43)
            timestamp = struct.unpack('!12I', data)[10]
            # Convert from NTP epoch (1900) to Unix epoch (1970)
            unix_time = timestamp - 2208988800
            client.close()
            return int(unix_time)
    except Exception as e:
        logger.debug(f"NTP {host} failed: {e}")
    return 0

def _get_http_time(url: str, timeout: int = 5) -> int:
    """Get time from HTTP Date header."""
    try:
        import requests
        import email.utils as eut
        
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if "Date" in response.headers:
            date_tuple = eut.parsedate_to_datetime(response.headers["Date"])
            return int(date_tuple.timestamp())
    except Exception as e:
        logger.debug(f"HTTP time from {url} failed: {e}")
    return 0

def _apply_time_offset():
    """Apply time offset to fix Telegram FloodWait and time sync issues."""
    ntp_sources = [
        "time.google.com",
        "time.cloudflare.com",
        "pool.ntp.org",
        "time.windows.com",
    ]
    
    http_sources = [
        "https://www.google.com",
        "https://www.cloudflare.com",
    ]
    
    real_time = 0
    source = "unknown"
    
    # Try NTP servers first (more accurate)
    for ntp_host in ntp_sources:
        real_time = _get_ntp_time(ntp_host)
        if real_time > 0:
            source = f"NTP ({ntp_host})"
            break
    
    # Fallback to HTTP if NTP fails
    if real_time == 0:
        for http_url in http_sources:
            real_time = _get_http_time(http_url)
            if real_time > 0:
                source = f"HTTP ({http_url})"
                break
    
    local_time = int(_time.time())
    offset = real_time - local_time if real_time > 0 else 0
    
    # Apply offset logic
    if real_time == 0:
        # Failed to get real time - force forward offset
        offset = 15
        logger.warning(f"⚠️  Could not fetch real time. Forcing +{offset}s offset to prevent time sync issues.")
    elif abs(offset) <= 2:
        # Time difference too small or container clock slightly behind
        offset = 10
        logger.info(f"🕒 Time difference small ({offset}s). Forcing +{offset}s offset as safety measure.")
    else:
        # Significant time difference detected
        logger.info(f"🕒 Time offset detected: {offset}s (Source: {source})")
        logger.info(f"   Real time: {real_time} | Local time: {local_time}")
    
    # Monkey-patch time.time()
    _original_time = _time.time
    _time.time = lambda: _original_time() + offset
    
    logger.info(f"✅ Time offset applied: +{offset}s")
    return offset

# Apply the time patch before starting the bot
try:
    _applied_offset = _apply_time_offset()
except Exception as e:
    logger.error(f"❌ Time patch failed: {e}")
    logger.warning("⚠️  Bot may experience FloodWait issues if system time is incorrect.")
# ---------------- END TIME PATCH ----------------

# Telegram client
app = Client(
    "gofile_pixeldrain_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60  # Handle FloodWait automatically up to 60s
)

# Health check endpoint for hosting platforms
async def health_check(request):
    return web.Response(text="Bot is running fine!", status=200)

async def run_http_server():
    """Run HTTP server for health checks (required by some hosting platforms)."""
    port = int(os.environ.get("PORT", 8080))
    server = web.Application()
    server.add_routes([web.get("/", health_check)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ Health check server running on port {port}")

async def main():
    """Main entry point."""
    try:
        # Start bot and HTTP server concurrently
        await asyncio.gather(
            app.start(),
            run_http_server()
        )
        logger.info("🤖 Bot started successfully!")
        logger.info(f"   Bot username: @{app.me.username}")
        logger.info(f"   Bot ID: {app.me.id}")
        
        # Keep the bot running
        await app.idle()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}", exc_info=True)
    finally:
        try:
            await app.stop()
            logger.info("👋 Bot stopped gracefully")
        except:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown complete")
