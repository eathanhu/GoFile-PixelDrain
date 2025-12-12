import os
import asyncio
from aiohttp import web
from pyrogram import Client
from pyrogram.raw.functions import Ping
from config import API_ID, API_HASH, BOT_TOKEN
import handlers  # registers handlers on import
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram client with proper configuration
logger.info("Creating Pyrogram client...")
app = Client(
    "gofile_pixeldrain_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,  # Automatically handle FloodWait up to 60s
    workdir=".",  # Store session in current directory
    in_memory=False  # Use persistent session file
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

async def test_connection():
    """Test Telegram connection using invoke() method with sleep_threshold."""
    try:
        logger.info("Testing Telegram connection...")
        # Use invoke() method with sleep_threshold like in the solution
        result = await app.invoke(Ping(ping_id=0), sleep_threshold=60)
        logger.info("✅ Telegram connection test successful!")
        return True
    except Exception as e:
        logger.error(f"❌ Telegram connection test failed: {e}")
        return False

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
        await app.start()
        
        # Test connection using invoke() method
        await test_connection()
        
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
