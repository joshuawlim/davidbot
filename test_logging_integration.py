#!/usr/bin/env python3
"""Test script to validate MessageLog integration and generate test data."""

import asyncio
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from davidbot.bot_handler import BotHandler
from davidbot.database import get_db_session, MessageLogRepository, FeedbackRepository
from davidbot.models import FeedbackEvent

async def test_message_logging():
    """Test message logging functionality."""
    print("🧪 Testing message logging integration...")
    
    bot = BotHandler()
    
    # Test search query logging
    user_id = "test_user_001"
    response = await bot.handle_message(user_id, "find songs on surrender")
    print(f"✅ Search response: {len(response)} songs returned")
    
    # Test "more" request logging
    response = await bot.handle_message(user_id, "more")
    print(f"✅ More response: {len(response)} messages returned")
    
    # Test feedback logging (should get latest songs from session)
    response = await bot.handle_message(user_id, "👍 1")
    print(f"✅ Feedback response: {response}")
    
    # Check database entries
    with get_db_session() as session:
        message_repo = MessageLogRepository(session)
        feedback_repo = FeedbackRepository(session)
        
        messages = message_repo.get_user_message_history(user_id, 10)
        print(f"📊 Found {len(messages)} message log entries")
        
        feedback = feedback_repo.get_user_feedback_history(user_id, 10)
        print(f"📊 Found {len(feedback)} feedback entries")

def generate_performance_test_data():
    """Generate test data to validate analytics performance on 10k+ records."""
    print("\n🏗️  Generating performance test data...")
    
    # Generate message types and users
    message_types = ['search', 'more', 'feedback', 'unknown']
    users = [f"perf_user_{i:04d}" for i in range(200)]  # 200 test users
    search_queries = [
        "find songs on surrender",
        "find songs on worship", 
        "find songs on grace",
        "find songs on love",
        "find songs on peace",
        "find songs on hope",
        "find songs on joy",
        "find songs on faith"
    ]
    
    with get_db_session() as session:
        message_repo = MessageLogRepository(session)
        
        # Generate 10,000+ message log entries
        start_date = datetime.now() - timedelta(days=365)  # Last year
        
        for i in range(10500):  # 10,500 records to exceed 10k requirement
            # Random timestamp in last year
            days_ago = random.randint(0, 365)
            timestamp = start_date + timedelta(days=days_ago)
            
            # Random user and message type
            user_id = random.choice(users)
            message_type = random.choice(message_types)
            
            if message_type == 'search':
                message_content = random.choice(search_queries)
                response_content = "Here are 3 songs for you:\n1. Song A\n2. Song B\n3. Song C"
            elif message_type == 'more':
                message_content = "more"
                response_content = "Here are 3 more songs:\n1. Song D\n2. Song E\n3. Song F"
            elif message_type == 'feedback':
                message_content = f"👍 {random.randint(1, 3)}"
                response_content = f"Thanks for the feedback on song {random.randint(1, 3)}!"
            else:
                message_content = "hello"
                response_content = "I can help you find songs. Try: 'find songs on surrender'"
            
            log_data = {
                'timestamp': timestamp,
                'user_id': user_id,
                'message_type': message_type,
                'message_content': message_content,
                'response_content': response_content,
                'session_context': None
            }
            
            message_repo.create(log_data)
            
            if i % 1000 == 0:
                print(f"Generated {i} records...")
                session.commit()  # Commit in batches
        
        # Final commit
        session.commit()
        print(f"✅ Generated {i + 1} test records")

def test_analytics_performance():
    """Test analytics query performance on the generated data."""
    print("\n⚡ Testing analytics performance...")
    
    with get_db_session() as session:
        message_repo = MessageLogRepository(session)
        
        # Test 1: Message type statistics
        start_time = datetime.now()
        stats = message_repo.get_message_type_stats(days=30)
        duration1 = (datetime.now() - start_time).total_seconds()
        print(f"📈 Message type stats (30 days): {stats}")
        print(f"⏱️  Query time: {duration1:.3f} seconds")
        
        # Test 2: Active users count
        start_time = datetime.now()
        users = message_repo.get_active_users_count(days=90)
        duration2 = (datetime.now() - start_time).total_seconds()
        print(f"👥 Active users (90 days): {users}")
        print(f"⏱️  Query time: {duration2:.3f} seconds")
        
        # Test 3: Recent activity
        start_time = datetime.now()
        activity = message_repo.get_recent_activity(limit=100)
        duration3 = (datetime.now() - start_time).total_seconds()
        print(f"📋 Recent activity: {len(activity)} records")
        print(f"⏱️  Query time: {duration3:.3f} seconds")
        
        # Test 4: Total record count
        start_time = datetime.now()
        from davidbot.database import MessageLog
        total = session.query(MessageLog).count()
        duration4 = (datetime.now() - start_time).total_seconds()
        print(f"📊 Total message logs: {total}")
        print(f"⏱️  Count query time: {duration4:.3f} seconds")
        
        # Performance validation
        max_time = max(duration1, duration2, duration3, duration4)
        if max_time < 1.0:
            print(f"\n✅ PERFORMANCE VALIDATION PASSED: Max query time {max_time:.3f}s < 1.0s")
        else:
            print(f"\n❌ PERFORMANCE VALIDATION FAILED: Max query time {max_time:.3f}s >= 1.0s")

async def main():
    """Run all integration and performance tests."""
    print("🚀 Sprint 1 Integration & Performance Validation")
    print("=" * 50)
    
    # Test 1: Message logging integration
    await test_message_logging()
    
    # Test 2: Generate performance test data
    with get_db_session() as session:
        from davidbot.database import MessageLog
        existing_count = session.query(MessageLog).count()
        if existing_count < 10000:
            generate_performance_test_data()
        else:
            print(f"📊 Using existing {existing_count} test records")
    
    # Test 3: Analytics performance validation
    test_analytics_performance()
    
    print("\n🎯 Sprint 1 Validation Complete!")

if __name__ == "__main__":
    asyncio.run(main())