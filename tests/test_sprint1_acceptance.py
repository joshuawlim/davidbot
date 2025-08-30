#!/usr/bin/env python3
"""
Sprint 1 Acceptance Test Suite

Validates all acceptance criteria:
1. A full query, response, and like on a recommendation is logged to database
2. Analytics queries run <1 second on 10k+ records  
3. CLI commands provide actionable insights
"""

import asyncio
import sys
import pytest
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from davidbot.bot_handler import BotHandler
from davidbot.database import get_db_session, MessageLogRepository, FeedbackRepository, SongRepository


class TestSprint1Acceptance:
    """Test suite for Sprint 1 acceptance criteria."""
    
    @pytest.fixture
    def bot_handler(self):
        """Create bot handler instance."""
        return BotHandler()
    
    @pytest.fixture
    def test_user_id(self):
        """Test user ID for consistent testing."""
        return "sprint1_test_user"
    
    async def test_full_query_response_like_logging_flow(self, bot_handler, test_user_id):
        """
        Acceptance Criteria 1: A full query, response, and like on a recommendation is logged to database
        
        Tests the complete user journey:
        1. User sends search query
        2. Bot responds with songs
        3. User likes a song
        4. All interactions are logged to database
        """
        # Step 1: User sends search query
        search_query = "find songs on surrender"
        search_response = await bot_handler.handle_message(test_user_id, search_query)
        
        assert isinstance(search_response, list)
        assert len(search_response) > 0
        print(f"✅ Search returned {len(search_response)} songs")
        
        # Step 2: User likes the first song (👍 1)
        like_response = await bot_handler.handle_message(test_user_id, "👍 1")
        
        assert isinstance(like_response, str)
        assert "thanks" in like_response.lower()
        print(f"✅ Like response: {like_response}")
        
        # Step 3: Verify all interactions logged to database
        with get_db_session() as session:
            message_repo = MessageLogRepository(session)
            feedback_repo = FeedbackRepository(session)
            
            # Check message logs (search + feedback)
            messages = message_repo.get_user_message_history(test_user_id, 10)
            search_logs = [m for m in messages if m.message_type == 'search']
            feedback_logs = [m for m in messages if m.message_type == 'feedback']
            
            assert len(search_logs) >= 1, "Search query not logged"
            assert len(feedback_logs) >= 1, "Feedback message not logged"
            
            # Check feedback database entries
            user_feedback = feedback_repo.get_user_feedback_history(test_user_id, 10)
            assert len(user_feedback) >= 1, "Feedback action not logged to database"
            
            latest_feedback = user_feedback[0]
            assert latest_feedback.action == 'thumbs_up'
            assert latest_feedback.user_id == test_user_id
            
            print(f"✅ Database logging verified:")
            print(f"   - Message logs: {len(messages)} entries")
            print(f"   - Feedback entries: {len(user_feedback)} entries")
    
    async def test_analytics_performance_on_10k_records(self):
        """
        Acceptance Criteria 2: Analytics queries run <1 second on 10k+ records
        
        Tests performance of key analytics operations on large dataset.
        """
        with get_db_session() as session:
            message_repo = MessageLogRepository(session)
            
            # Verify we have 10k+ records
            from davidbot.database import MessageLog
            total_records = session.query(MessageLog).count()
            assert total_records >= 10000, f"Need 10k+ records, found {total_records}"
            print(f"✅ Testing on {total_records} message records")
            
            # Test 1: Message type statistics (complex aggregation)
            start_time = datetime.now()
            stats = message_repo.get_message_type_stats(days=365)
            duration1 = (datetime.now() - start_time).total_seconds()
            
            assert duration1 < 1.0, f"Message stats query took {duration1:.3f}s > 1.0s"
            assert len(stats) > 0, "No statistics returned"
            print(f"✅ Message type stats: {duration1:.3f}s < 1.0s")
            
            # Test 2: Active users count (distinct aggregation)
            start_time = datetime.now()
            users = message_repo.get_active_users_count(days=365)
            duration2 = (datetime.now() - start_time).total_seconds()
            
            assert duration2 < 1.0, f"Active users query took {duration2:.3f}s > 1.0s"
            assert users > 0, "No active users found"
            print(f"✅ Active users count: {duration2:.3f}s < 1.0s")
            
            # Test 3: Recent activity (ordered query with limit)
            start_time = datetime.now()
            activity = message_repo.get_recent_activity(limit=1000)
            duration3 = (datetime.now() - start_time).total_seconds()
            
            assert duration3 < 1.0, f"Recent activity query took {duration3:.3f}s > 1.0s"
            assert len(activity) > 0, "No recent activity found"
            print(f"✅ Recent activity query: {duration3:.3f}s < 1.0s")
            
            max_duration = max(duration1, duration2, duration3)
            print(f"✅ All analytics queries under 1 second (max: {max_duration:.3f}s)")
    
    def test_cli_commands_provide_actionable_insights(self):
        """
        Acceptance Criteria 3: CLI commands provide actionable insights
        
        Tests that CLI management commands provide meaningful business insights.
        """
        import subprocess
        
        # Test 1: Database info command
        result = subprocess.run(
            ["python3", "src/davidbot/manage.py", "info"], 
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0, f"Info command failed: {result.stderr}"
        
        output = result.stdout
        assert "songs:" in output, "Song count not shown"
        assert "message_logs:" in output, "Message log count not shown"
        print("✅ Database info provides record counts")
        
        # Test 2: Familiarity scores (actionable for worship planning)
        result = subprocess.run(
            ["python3", "src/davidbot/manage.py", "familiarity"], 
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0, f"Familiarity command failed: {result.stderr}"
        
        output = result.stdout
        assert "Score:" in output, "Familiarity scores not shown"
        assert "/10.0" in output, "Score format not correct"
        print("✅ Familiarity command provides worship planning insights")
        
        # Test 3: Usage statistics (actionable for trend analysis)
        result = subprocess.run(
            ["python3", "src/davidbot/manage.py", "usage-stats"], 
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0, f"Usage stats command failed: {result.stderr}"
        
        output = result.stdout
        assert "Total song uses:" in output, "Usage totals not shown"
        assert "Top songs" in output, "Popular songs not shown"
        print("✅ Usage stats provide trend analysis insights")
        
        # Test 4: Themes command (actionable for content categorization)
        result = subprocess.run(
            ["python3", "src/davidbot/manage.py", "themes"], 
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0, f"Themes command failed: {result.stderr}"
        
        output = result.stdout
        assert len(output.strip()) > 0, "No themes output"
        print("✅ Themes command provides content categorization insights")
        
        print("✅ All CLI commands provide actionable business insights")


async def run_acceptance_tests():
    """Run all Sprint 1 acceptance tests."""
    print("🎯 SPRINT 1 ACCEPTANCE TEST SUITE")
    print("=" * 50)
    
    test_suite = TestSprint1Acceptance()
    bot_handler = BotHandler()
    test_user_id = f"acceptance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Test 1: Full logging flow
        print("\n1️⃣  Testing full query/response/like logging flow...")
        await test_suite.test_full_query_response_like_logging_flow(bot_handler, test_user_id)
        print("✅ ACCEPTANCE CRITERIA 1: PASSED")
        
        # Test 2: Analytics performance  
        print("\n2️⃣  Testing analytics performance on 10k+ records...")
        await test_suite.test_analytics_performance_on_10k_records()
        print("✅ ACCEPTANCE CRITERIA 2: PASSED")
        
        # Test 3: CLI insights
        print("\n3️⃣  Testing CLI commands provide actionable insights...")
        test_suite.test_cli_commands_provide_actionable_insights()
        print("✅ ACCEPTANCE CRITERIA 3: PASSED")
        
        print("\n🏆 ALL SPRINT 1 ACCEPTANCE CRITERIA PASSED!")
        print("Ready for production deployment.")
        
    except Exception as e:
        print(f"\n❌ ACCEPTANCE TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_acceptance_tests())