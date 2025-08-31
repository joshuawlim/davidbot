"""Main entry point for DavidBot."""

import os
import signal
import asyncio
import logging
import aiohttp
from dotenv import load_dotenv

from .bot_handler import BotHandler
from .enhanced_bot_handler import create_enhanced_bot_handler
from .sheets_client import SheetsClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def _check_ollama_availability(ollama_url: str) -> bool:
    """Check if Ollama service is available and has required models."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ollama_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    logger.info(f"Ollama available with models: {', '.join(models[:3])}...")
                    return len(models) > 0
                else:
                    logger.warning(f"Ollama service returned {response.status}")
                    return False
    except Exception as e:
        logger.warning(f"Ollama service unavailable: {e}")
        return False


async def main():
    """Main function to run DavidBot."""
    logger.info("Starting DavidBot...")
    
    # Check for required environment variables
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        logger.error("Please set your bot token in the .env file")
        return
    
    # Check for Ollama service availability for enhanced features
    ollama_url = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
    use_enhanced_handler = await _check_ollama_availability(ollama_url)
    
    if use_enhanced_handler:
        logger.info(f"Ollama service available at {ollama_url} - using enhanced bot handler with natural language processing")
        bot_handler = create_enhanced_bot_handler(ollama_url, use_mock_llm=False)
    else:
        logger.info(f"Ollama service not available at {ollama_url} - using enhanced handler with mock LLM")
        bot_handler = create_enhanced_bot_handler(ollama_url, use_mock_llm=True)
    
    logger.info("DavidBot initialized successfully")
    logger.info("Starting Telegram long polling...")
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, requesting graceful shutdown...")
        bot_handler.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the bot with long polling
        await bot_handler.start_polling(telegram_token)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        bot_handler.shutdown()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        logger.info("DavidBot shutting down gracefully")


if __name__ == "__main__":
    asyncio.run(main())