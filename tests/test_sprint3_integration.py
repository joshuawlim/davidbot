#!/usr/bin/env python3
"""Comprehensive Sprint 3 integration test."""

import asyncio
import sys
import os
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from davidbot.enhanced_bot_handler import create_enhanced_bot_handler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_sprint3_features():
    """Test all Sprint 3 deliverables."""
    print("🎵 SPRINT 3 COMPREHENSIVE INTEGRATION TEST")
    print("="*60)
    
    # Test 1: Enhanced Bot Handler Creation
    print("\n1️⃣ Testing Enhanced Bot Handler Creation...")
    try:
        bot_handler = create_enhanced_bot_handler("http://127.0.0.1:11434", use_mock_llm=False)
        print("✅ Enhanced bot handler created successfully")
    except Exception as e:
        print(f"❌ Failed to create enhanced bot handler: {e}")
        return False
    
    # Test 2: Natural Language Processing
    print("\n2️⃣ Testing Natural Language Processing...")
    test_queries = [
        ("find songs about surrender", ["surrender"], "ministry"),
        ("upbeat celebration songs", ["celebration", "joy"], "celebration"),
        ("songs for altar call", ["worship"], "worship")
    ]
    
    user_id = "test_sprint3_user"
    for query, expected_themes, expected_context in test_queries:
        try:
            response = await bot_handler.handle_message(user_id, query)
            if isinstance(response, list) and len(response) > 1:
                # Check for ministry context intro
                intro = response[0]
                songs = response[1:]
                
                print(f"✅ Query: '{query}'")
                print(f"   Context: {intro}")
                print(f"   Songs found: {len(songs)}")
                
                # Verify ministry context
                ministry_words = ["ministry", "celebration", "worship", "faith", "love"]
                has_ministry_context = any(word in intro.lower() for word in ministry_words)
                if has_ministry_context:
                    print(f"   ✅ Ministry context detected")
                else:
                    print(f"   ⚠️ No ministry context")
            else:
                print(f"❌ Unexpected response format for '{query}'")
                
        except Exception as e:
            print(f"❌ Failed query '{query}': {e}")
    
    # Test 3: Conversational Context
    print("\n3️⃣ Testing Conversational Context...")
    try:
        # First search
        await bot_handler.handle_message(user_id, "find worship songs")
        
        # Follow-up request
        response = await bot_handler.handle_message(user_id, "more")
        if response:
            print("✅ 'More' request handled with context")
        else:
            print("❌ 'More' request failed")
            
        # Feedback
        response = await bot_handler.handle_message(user_id, "👍 2")
        if "thanks" in response.lower() or "noted" in response.lower():
            print("✅ Feedback processed successfully")
        else:
            print("❌ Feedback processing failed")
            
    except Exception as e:
        print(f"❌ Conversational context test failed: {e}")
    
    # Test 4: Fallback System
    print("\n4️⃣ Testing Fallback System...")
    try:
        # Create bot with mock LLM (simulating Ollama unavailable)
        fallback_bot = create_enhanced_bot_handler("http://127.0.0.1:11434", use_mock_llm=True)
        response = await fallback_bot.handle_message(user_id, "find surrender songs")
        
        if response and len(response) > 1:
            print("✅ Fallback system working")
        else:
            print("❌ Fallback system failed")
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
    
    print("\n" + "="*60)
    print("🏁 SPRINT 3 INTEGRATION TEST COMPLETE")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_sprint3_features())