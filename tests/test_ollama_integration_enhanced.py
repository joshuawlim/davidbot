#!/usr/bin/env python3
"""Test script for Ollama integration with enhanced bot handler."""

import asyncio
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from davidbot.enhanced_bot_handler import create_enhanced_bot_handler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ollama_integration():
    """Test enhanced bot handler with Ollama integration."""
    print("=" * 60)
    print("TESTING OLLAMA INTEGRATION FOR SPRINT 3")
    print("=" * 60)
    
    # Create enhanced bot handler with Ollama
    print("\n1. Creating enhanced bot handler...")
    bot_handler = create_enhanced_bot_handler("http://127.0.0.1:11434", use_mock_llm=False)
    
    # Test queries that should demonstrate natural language processing
    test_queries = [
        "find songs about surrender",
        "upbeat songs for celebration", 
        "slow songs about grace",
        "songs for altar call",
        "praise songs in G",
        "something like Amazing Grace",
        "songs we haven't used lately",
        "need worship songs for ministry moment",
        "celebration songs for baptism",
        "songs about God's love"
    ]
    
    print(f"\n2. Testing {len(test_queries)} natural language queries...\n")
    
    user_id = "test_user_123"
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: '{query}'")
        print("-" * 50)
        
        try:
            start_time = asyncio.get_event_loop().time()
            response = await bot_handler.handle_message(user_id, query)
            end_time = asyncio.get_event_loop().time()
            
            processing_time = (end_time - start_time) * 1000
            
            print(f"Response time: {processing_time:.0f}ms")
            
            if isinstance(response, list):
                for j, msg in enumerate(response):
                    print(f"Response {j+1}: {msg}")
            else:
                print(f"Response: {response}")
            
            print()
            
        except Exception as e:
            print(f"ERROR: {e}")
            print()
    
    print("=" * 60)
    print("OLLAMA INTEGRATION TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ollama_integration())