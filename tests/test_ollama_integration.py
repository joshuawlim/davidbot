#!/usr/bin/env python3
"""Test script for Ollama integration with DavidBot."""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from davidbot.llm_query_parser import LLMQueryParser
from davidbot.enhanced_bot_handler import create_enhanced_bot_handler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def test_ollama_parser():
    """Test the Ollama LLM query parser."""
    logger.info("Testing Ollama LLM Query Parser...")
    
    parser = LLMQueryParser()
    
    test_queries = [
        "find songs on surrender",
        "upbeat songs for celebration", 
        "slow songs about grace",
        "Holy Spirit",
        "something like Amazing Grace",
        "more songs"
    ]
    
    for query in test_queries:
        logger.info(f"\nTesting: '{query}'")
        try:
            result = await parser.parse(query)
            logger.info(f"  Intent: {result.intent}")
            logger.info(f"  Themes: {result.themes}")
            logger.info(f"  BPM: {result.bpm_min}-{result.bpm_max}")
            logger.info(f"  Confidence: {result.confidence}")
        except Exception as e:
            logger.error(f"  Error: {e}")


async def test_enhanced_bot_handler():
    """Test the enhanced bot handler with Ollama."""
    logger.info("\nTesting Enhanced Bot Handler...")
    
    try:
        bot = create_enhanced_bot_handler()
        
        test_messages = [
            "find songs on surrender",
            "upbeat celebration songs",
            "Holy Spirit"
        ]
        
        user_id = "test_user"
        
        for message in test_messages:
            logger.info(f"\nTesting message: '{message}'")
            try:
                response = await bot.handle_message(user_id, message)
                if isinstance(response, list):
                    logger.info(f"  Response ({len(response)} messages):")
                    for i, resp in enumerate(response[:2], 1):  # Show first 2
                        logger.info(f"    {i}: {resp[:100]}...")
                else:
                    logger.info(f"  Response: {response}")
            except Exception as e:
                logger.error(f"  Error: {e}")
                
    except Exception as e:
        logger.error(f"Failed to create bot handler: {e}")


async def main():
    """Run all tests."""
    logger.info("Starting Ollama integration tests...")
    
    # Test 1: Direct parser test
    await test_ollama_parser()
    
    # Test 2: Full bot handler test
    await test_enhanced_bot_handler()
    
    logger.info("\nTests completed!")


if __name__ == "__main__":
    asyncio.run(main())