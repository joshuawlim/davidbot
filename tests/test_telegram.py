#!/usr/bin/env python3
"""Test Telegram bot connection."""

import asyncio
import aiohttp
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

async def test_telegram_connection():
    """Test basic connection to Telegram API."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        return False
    
    api_url = f"https://api.telegram.org/bot{token}"
    
    # Create SSL context - disable verification for development/corporate networks
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(f"{api_url}/getMe") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        bot_info = data.get("result", {})
                        print(f"✅ Bot connection successful!")
                        print(f"   Bot name: {bot_info.get('first_name')}")
                        print(f"   Bot username: @{bot_info.get('username')}")
                        return True
                    else:
                        print(f"❌ Telegram API error: {data}")
                        return False
                else:
                    print(f"❌ HTTP error {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())