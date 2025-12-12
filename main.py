import os
import asyncio
from aiohttp import web
from pyrogram import Client
from pyrogram.raw.functions import Ping
from config import API_ID, API_HASH, BOT_TOKEN
import handlers  # registers handlers on import
import logging

# ============= CRITICAL TIME FIX (MUST BE BEFORE IMPORTS) =============
import time as _time

# Force time forward by 60 seconds to prevent msg_id errors on Render
_OFFSET = 60
_original_time = _time.time
_time.time = lambda: _original_time() + _OFFSET

print(f"⏰ Time offset applied: +{_OFFSET}s")
print(f"   System time: {int(_original_time())}")
print(f"   Adjusted time: {int(_time.time())}")
# ======================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram client - MUST be created AFTER time patch
logger.info("Creating Pyrogram client with time offset...")
app = Client(
    "gofile_pixeldrain_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,  # Handle FloodWait automatically
    workdir=".",
    in_memory=False
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
    
    logger.info(f"✅ HTTP server started on 0.0.0.0:{port}")

async def test_connection():
    """Test Telegram connection."""
    try:
        logger.info("Testing Telegram connection with invoke()...")
        result = await app.invoke(Ping(ping_id=0), sleep_threshold=60)
        logger.info("✅ Connection test successful!")
        return True
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("🚀 GoFile-PixelDrain Bot Starting...")
    logger.info(f"   Time offset: +{_OFFSET}s")
    logger.info(f"   Current timestamp: {int(_time.time())}")
    logger.info("=" * 60)
    
    try:
        # Start HTTP server FIRST (Render needs this immediately)
        logger.info("Starting HTTP health check server...")
        asyncio.create_task(run_http_server())
        await asyncio.sleep(2)  # Give server time to start
        
        # Start Telegram client
        logger.info("Starting Telegram client...")
        await app.start()
        
        # Test connection
        await test_connection()
        
        logger.info("=" * 60)
        logger.info("🤖 BOT STARTED SUCCESSFULLY!")
        logger.info(f"   Username: @{app.me.username}")
        logger.info(f"   Bot ID: {app.me.id}")
        logger.info(f"   Name: {app.me.first_name}")
        logger.info("=" * 60)
        logger.info("✅ ALL SERVICES RUNNING")
        logger.info("=" * 60)
        
        # Keep running
        await app.idle()
        
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}", exc_info=True)
        raise
    finally:
        try:
            logger.info("Stopping bot...")
            await app.stop()
            logger.info("👋 Bot stopped")
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
