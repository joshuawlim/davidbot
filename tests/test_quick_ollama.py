#!/usr/bin/env python3
"""Quick test of Ollama integration fixes."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from davidbot.llm_query_parser import LLMQueryParser

async def test_quick():
    parser = LLMQueryParser("http://127.0.0.1:11434")
    
    print("Testing 3 quick queries with improved Ollama setup...")
    
    queries = [
        "find songs about surrender",
        "upbeat celebration songs", 
        "slow grace worship"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        result = await parser.parse(query)
        print(f"Themes: {result.themes}")
        print(f"Intent: {result.intent}")
        print(f"Confidence: {result.confidence}")
        print(f"BPM: {result.bpm_min}-{result.bpm_max}")

if __name__ == "__main__":
    asyncio.run(test_quick())