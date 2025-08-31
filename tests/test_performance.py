"""Performance tests for enhanced bot handler."""

import pytest
import asyncio
import time
from src.davidbot.enhanced_bot_handler import create_enhanced_bot_handler


class TestPerformance:
    """Test performance requirements for enhanced bot."""
    
    @pytest.mark.asyncio
    async def test_mock_llm_response_time(self):
        """Test that mock LLM responses are under 2 seconds."""
        bot_handler = create_enhanced_bot_handler(use_mock_llm=True)
        
        test_queries = [
            'find songs on worship',
            'upbeat songs for celebration',
            'slow songs about grace',
            'songs like Amazing Grace',
            'more songs',
            'the second one was perfect'
        ]
        
        for query in test_queries:
            start_time = time.time()
            response = await bot_handler.handle_message('perf_user', query)
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"Query: '{query}' took {response_time:.3f}s")
            
            # Should be well under 2 seconds with mock LLM
            assert response_time < 2.0, f"Response time {response_time:.3f}s exceeded 2.0s for query: '{query}'"
            assert response is not None
    
    @pytest.mark.asyncio 
    async def test_concurrent_requests(self):
        """Test performance under concurrent load."""
        bot_handler = create_enhanced_bot_handler(use_mock_llm=True)
        
        async def single_request(user_id: str, query: str):
            start_time = time.time()
            response = await bot_handler.handle_message(user_id, query)
            end_time = time.time()
            return end_time - start_time, response
        
        # Test 5 concurrent requests
        tasks = []
        for i in range(5):
            task = single_request(f'user{i}', 'find songs on worship')
            tasks.append(task)
        
        start_concurrent = time.time()
        results = await asyncio.gather(*tasks)
        end_concurrent = time.time()
        
        total_concurrent_time = end_concurrent - start_concurrent
        print(f"5 concurrent requests completed in {total_concurrent_time:.3f}s")
        
        # All individual requests should be under 2s
        for i, (response_time, response) in enumerate(results):
            print(f"Concurrent request {i}: {response_time:.3f}s")
            assert response_time < 2.0
            assert response is not None
        
        # Total concurrent time should be reasonable (not much more than single request)
        assert total_concurrent_time < 5.0  # Generous limit for concurrent processing
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self):
        """Test that database queries are performant."""
        bot_handler = create_enhanced_bot_handler(use_mock_llm=True)
        
        # Test multiple different searches to exercise database
        search_terms = ['worship', 'praise', 'grace', 'love', 'peace', 'joy', 'hope', 'faith']
        
        total_start = time.time()
        
        for term in search_terms:
            start_time = time.time()
            response = await bot_handler.handle_message('db_user', f'find songs on {term}')
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"Database search for '{term}': {response_time:.3f}s")
            
            assert response_time < 2.0
            assert isinstance(response, list)
            assert len(response) > 0
        
        total_end = time.time()
        total_time = total_end - total_start
        average_time = total_time / len(search_terms)
        
        print(f"Average database search time: {average_time:.3f}s")
        assert average_time < 1.0  # Should be well under 1 second on average


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])  # -s to show print output