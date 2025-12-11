import os
import asyncio
from aiohttp import web
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import handlers  # registers handlers on import

# ---------------- CRITICAL TIME-SYNC FIX ----------------
import time as _time
import socket
import struct
import logging

import logging
from pyrogram.errors import RPCError

logger = logging.getLogger(__name__)

def valid_msg_id(msg_id) -> bool:
    """Return True if msg_id looks valid for Telegram APIs."""
    try:
        return isinstance(msg_id, int) and msg_id > 0
    except Exception:
        return False

async def safe_get_message(client, chat_id, msg_id):
    """Return Message or None. Handles MSG_ID_TOO_LOW / invalid IDs gracefully."""
    if not valid_msg_id(msg_id):
        logger.warning("safe_get_message: invalid message id: %r", msg_id)
        return None
    try:
        return await client.get_messages(chat_id, msg_id)
    except RPCError as e:
        txt = str(e)
        if "MSG_ID_TOO_LOW" in txt or "MessageIdInvalid" in txt or "msg_id too low" in txt.lower():
            logger.warning("safe_get_message: msg id too low/invalid for %s: %s", chat_id, msg_id)
            return None
        logger.exception("safe_get_message: unexpected RPCError for %s:%s", chat_id, msg_id)
        return None
    except Exception:
        logger.exception("safe_get_message: unexpected error")
        return None

async def safe_forward(client, from_chat, to_chat, msg_id):
    """Try to forward a message but skip if msg id invalid/too low."""
    if not valid_msg_id(msg_id):
        logger.warning("safe_forward: invalid msg id %r, skipping", msg_id)
        return None
    try:
        await client.forward_messages(chat_id=to_chat, from_chat_id=from_chat, message_ids=msg_id)
        return True
    except RPCError as e:
        txt = str(e)
        if "MSG_ID_TOO_LOW" in txt or "MessageIdInvalid" in txt:
            logger.warning("safe_forward: msg id too low/invalid: %s -> %s id=%s", from_chat, to_chat, msg_id)
            return None
        logger.exception("safe_forward: unexpected RPCError")
        raise
    except Exception:
        logger.exception("safe_forward: unexpected error")
        raise

async def safe_edit(client, chat_id, msg_id, new_text, **kwargs):
    """Try to edit message, but handle stale/too low ids."""
    if not valid_msg_id(msg_id):
        logger.warning("safe_edit: invalid msg id %r, skipping", msg_id)
        return None
    try:
        msg = await client.get_messages(chat_id, msg_id)
        if msg is None:
            logger.warning("safe_edit: message not found %s:%s", chat_id, msg_id)
            return None
        await msg.edit(new_text, **kwargs)
        return True
    except RPCError as e:
        txt = str(e)
        if "MSG_ID_TOO_LOW" in txt or "MessageIdInvalid" in txt or "MESSAGE_NOT_MODIFIED" in txt:
            logger.warning("safe_edit: cannot edit (too low/invalid/not editable): %s:%s", chat_id, msg_id)
            return None
        logger.exception("safe_edit: unexpected RPCError")
        raise
    except Exception:
        logger.exception("safe_edit: unexpected error")
        raise
#remove from here -up
async def safe_delete(client, chat_id, msg_id, **kwargs):
    """Delete message safely; returns True if deleted else None."""
    if not valid_msg_id(msg_id):
        logger.warning("safe_delete: invalid msg id %r, skipping", msg_id)
        return None
    try:
        await client.delete_messages(chat_id, msg_id, **kwargs)
        return True
    except RPCError as e:
        txt = str(e)
        if "MSG_ID_TOO_LOW" in txt or "MessageIdInvalid" in txt or "Message to delete not found" in txt:
            logger.warning("safe_delete: msg id too low/invalid or already deleted: %s:%s", chat_id, msg_id)
            return None
        logger.exception("safe_delete: unexpected RPCError")
        raise
    except Exception:
        logger.exception("safe_delete: unexpected error")
        raise


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _get_ntp_time(host: str, port: int = 123, timeout: int = 10) -> int:
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

def _get_http_time(url: str, timeout: int = 10) -> int:
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
    """Apply time offset to fix Telegram msg_id sync issues."""
    ntp_sources = [
        "time.google.com",
        "time.cloudflare.com",
        "time.nist.gov",
        "pool.ntp.org",
    ]
    
    http_sources = [
        "https://www.google.com",
        "https://www.cloudflare.com",
    ]
    
    real_time = 0
    source = "unknown"
    
    # Try NTP servers first (most accurate)
    logger.info("🕒 Attempting to sync time with NTP servers...")
    for ntp_host in ntp_sources:
        logger.info(f"   Trying {ntp_host}...")
        real_time = _get_ntp_time(ntp_host, timeout=8)
        if real_time > 0:
            source = f"NTP ({ntp_host})"
            logger.info(f"   ✅ Success!")
            break
    
    # Fallback to HTTP if NTP fails
    if real_time == 0:
        logger.warning("⚠️  NTP failed, trying HTTP fallback...")
        for http_url in http_sources:
            logger.info(f"   Trying {http_url}...")
            real_time = _get_http_time(http_url, timeout=8)
            if real_time > 0:
                source = f"HTTP ({http_url})"
                logger.info(f"   ✅ Success!")
                break
    
    local_time = int(_time.time())
    offset = real_time - local_time if real_time else 0
    
    # Apply offset logic - CRITICAL for Render's clock issues
    if real_time == 0:
        # Failed to get real time - force significant forward offset
        offset = 30  # Increased from 15 to 30 for safety
        logger.warning(f"⚠️  Could not sync with any time source!")
        logger.warning(f"⚠️  Forcing +{offset}s offset to prevent msg_id errors")
    elif abs(offset) <= 5:
        # Time difference too small - Render containers often lag by a few seconds
        offset = 25  # Force forward offset for safety
        logger.info(f"🕒 Time difference: {offset}s (small)")
        logger.info(f"🕒 Forcing +25s offset as safety buffer for Render")
    else:
        # Significant time difference detected - use calculated offset
        # But add extra buffer if behind
        if offset < 0:
            offset = abs(offset) + 15  # Add 15s buffer if clock is behind
            logger.info(f"🕒 Clock is BEHIND by {abs(offset - 15)}s")
            logger.info(f"🕒 Applying {offset}s offset (with +15s safety buffer)")
        else:
            logger.info(f"🕒 Clock is AHEAD by {offset}s")
            logger.info(f"🕒 Applying {offset}s offset")
        logger.info(f"   Source: {source}")
        logger.info(f"   Real time: {real_time}")
        logger.info(f"   Local time: {local_time}")
    
    # Monkey-patch time.time() to fix msg_id generation
    _original_time = _time.time
    _time.time = lambda: _original_time() + offset
    
    logger.info(f"✅ Time offset applied: +{offset}s")
    logger.info(f"   New time: {int(_time.time())}")
    return offset

# CRITICAL: Apply time patch BEFORE creating Pyrogram client
try:
    _applied_offset = _apply_time_offset()
except Exception as e:
    logger.error(f"❌ Time patch failed: {e}")
    logger.warning("⚠️  Forcing default +30s offset as last resort")
    _original_time = _time.time
    _time.time = lambda: _original_time() + 30
# ---------------- END TIME PATCH ----------------

# Telegram client - MUST be created AFTER time patch
logger.info("Creating Pyrogram client...")
app = Client(
    "gofile_pixeldrain_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,  # Handle FloodWait automatically
    workdir="."  # Store session in current directory
)

# Health check endpoint for Render
async def health_check(request):
    """Health check endpoint - CRITICAL for Render deployment."""
    return web.Response(
        text="OK - Bot is running",
        status=200,
        content_type="text/plain"
    )

async def run_http_server():
    """Run HTTP server for health checks (required by Render)."""
    port = int(os.environ.get("PORT", 8080))
    
    server = web.Application()
    server.add_routes([
        web.get("/", health_check),
        web.get("/health", health_check),
        web.get("/ping", health_check),
    ])
    
    runner = web.AppRunner(server)
    await runner.setup()
    
    # IMPORTANT: Bind to 0.0.0.0 for Render
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info(f"✅ HTTP server started successfully")
    logger.info(f"   Listening on: 0.0.0.0:{port}")
    logger.info(f"   Health check: /")

async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("🚀 Starting GoFile-PixelDrain Bot on Render")
    logger.info("=" * 60)
    
    try:
        # Start HTTP server FIRST so Render sees it immediately
        logger.info("Starting HTTP health check server...")
        http_task = asyncio.create_task(run_http_server())
        
        # Give HTTP server time to bind to port
        await asyncio.sleep(2)
        
        # Now start the Telegram bot
        logger.info("Starting Telegram client...")
        logger.info(f"   Current time: {int(_time.time())}")
        
        await app.start()
        
        logger.info("=" * 60)
        logger.info("🤖 Bot started successfully!")
        logger.info(f"   Username: @{app.me.username}")
        logger.info(f"   Bot ID: {app.me.id}")
        logger.info(f"   First name: {app.me.first_name}")
        logger.info("=" * 60)
        logger.info("✅ ALL SERVICES RUNNING - Bot is ready!")
        logger.info("=" * 60)
        
        # Keep the bot running
        await app.idle()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}", exc_info=True)
        raise
    finally:
        try:
            await app.stop()
            logger.info("👋 Bot stopped gracefully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)
