"""Main entry point for DavidBot."""

import os
import asyncio
import logging
from dotenv import load_dotenv

from .bot_handler import BotHandler
from .sheets_client import SheetsClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run DavidBot."""
    logger.info("Starting DavidBot...")
    
    # Check for required environment variables
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        logger.error("Please set your bot token in the .env file")
        return
    
    # Initialize sheets client
    sheets_client = SheetsClient(fail_gracefully=True)
    
    # Initialize bot handler
    bot_handler = BotHandler(sheets_client=sheets_client)
    
    logger.info("DavidBot initialized successfully")
    logger.info("Starting Telegram long polling...")
    
    try:
        # Start the bot with long polling
        await bot_handler.start_polling(telegram_token)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        logger.info("DavidBot shutting down")


if __name__ == "__main__":
    asyncio.run(main())