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
    
    # Initialize sheets client
    sheets_client = SheetsClient(fail_gracefully=True)
    
    # Initialize bot handler
    bot_handler = BotHandler(sheets_client=sheets_client)
    
    logger.info("DavidBot initialized successfully")
    
    # Example usage - in production this would be replaced with Telegram bot integration
    while True:
        try:
            user_input = input("Enter user_id:message (or 'quit' to exit): ")
            if user_input.lower() == 'quit':
                break
                
            if ':' not in user_input:
                print("Please use format: user_id:message")
                continue
                
            user_id, message = user_input.split(':', 1)
            
            response = await bot_handler.handle_message(user_id.strip(), message.strip())
            print(f"Bot response: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            
    logger.info("DavidBot shutting down")


if __name__ == "__main__":
    asyncio.run(main())