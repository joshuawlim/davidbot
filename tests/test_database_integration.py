#!/usr/bin/env python3
"""Test database integration with bot handler."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from davidbot.database_recommendation_engine import DatabaseRecommendationEngine, create_recommendation_engine
from davidbot.bot_handler import BotHandler


def test_database_engine():
    """Test database recommendation engine directly."""
    print("=== Testing Database Recommendation Engine ===")
    
    engine = DatabaseRecommendationEngine()
    
    # Health check
    health = engine.health_check()
    print(f"Health Status: {health['status']}")
    print(f"Song Count: {health['song_count']}")
    print(f"Theme Count: {health['theme_count']}")
    print(f"Available Themes: {health.get('themes', [])}")
    
    # Test search
    print("\n--- Testing Search: 'surrender' ---")
    result = engine.search("find songs on surrender")
    if result:
        print(f"Matched Term: {result.matched_term}")
        print(f"Songs Found: {len(result.songs)}")
        for i, song in enumerate(result.songs, 1):
            print(f"  {i}. {song.title} - {song.artist} ({song.key}, {song.bpm} BPM)")
    else:
        print("No results found!")
    
    # Test follow-up search (with exclusions)
    print("\n--- Testing Follow-up Search: 'more' ---")
    excluded = [song.title for song in result.songs] if result else []
    more_result = engine.search("find songs on surrender", excluded_songs=excluded)
    if more_result:
        print(f"Additional Songs Found: {len(more_result.songs)}")
        for i, song in enumerate(more_result.songs, 1):
            print(f"  {i}. {song.title} - {song.artist} ({song.key}, {song.bpm} BPM)")
    else:
        print("No additional results found!")


def test_bot_handler():
    """Test bot handler with database integration."""
    print("\n=== Testing Bot Handler with Database ===")
    
    handler = BotHandler()
    
    # Test search through bot handler
    print("\n--- Testing Bot Search ---")
    
    import asyncio
    
    async def run_bot_tests():
        user_id = "test_user_123"
        
        # Search for surrender songs
        response1 = await handler.handle_message(user_id, "find songs on surrender")
        print(f"Bot Response 1:\n{response1}\n")
        
        # Ask for more
        response2 = await handler.handle_message(user_id, "more")
        print(f"Bot Response 2:\n{response2}\n")
        
        # Test feedback
        response3 = await handler.handle_message(user_id, "👍 1")
        print(f"Bot Response 3:\n{response3}\n")
    
    asyncio.run(run_bot_tests())


def main():
    """Run integration tests."""
    try:
        test_database_engine()
        test_bot_handler()
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()