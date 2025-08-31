#!/bin/bash

# DavidBot Startup Script
# Usage: ./start_davidbot.sh [TOKEN]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🤖 DavidBot Startup Script${NC}"
echo -e "${BLUE}=============================${NC}"

# Check if we're in the right directory
if [[ ! -f "$SCRIPT_DIR/src/davidbot/bot_handler.py" ]]; then
    echo -e "${RED}❌ Error: Cannot find DavidBot source files${NC}"
    echo -e "${RED}   Make sure you're running this from the DavidBot root directory${NC}"
    exit 1
fi

# Load environment variables from .env file
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    echo -e "${GREEN}📄 Loading environment variables from .env${NC}"
    # Export variables from .env file
    set -a  # automatically export all variables
    source "$SCRIPT_DIR/.env"
    set +a  # stop automatically exporting
else
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
fi

# Get Telegram bot token - DON'T reset it to empty after loading .env!
# Check if token provided as argument
if [[ $# -eq 1 ]]; then
    TELEGRAM_BOT_TOKEN="$1"
    echo -e "${GREEN}📋 Using token from command line argument${NC}"
# Check if token in environment variable (could be from .env)
elif [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    echo -e "${GREEN}📋 Using token from .env file${NC}"
# Prompt for token
else
    echo -e "${YELLOW}🔑 Telegram Bot Token Required${NC}"
    echo "Options to provide your token:"
    echo "1. Create a .env file with: TELEGRAM_BOT_TOKEN=your_token_here"
    echo "2. Set environment variable: export TELEGRAM_BOT_TOKEN=your_token"
    echo "3. Pass as argument: ./start_davidbot.sh your_token"
    echo "4. Enter it now when prompted"
    echo ""
    echo "Get your token from @BotFather on Telegram: https://t.me/botfather"
    echo ""
    read -p "Enter your Telegram bot token: " TELEGRAM_BOT_TOKEN
fi

# Validate token format (basic check)
if [[ ! $TELEGRAM_BOT_TOKEN =~ ^[0-9]+:[A-Za-z0-9_-]{35}$ ]]; then
    echo -e "${RED}❌ Error: Invalid token format${NC}"
    echo -e "${RED}   Token should look like: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11${NC}"
    exit 1
fi

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Error: Python not found${NC}"
    echo -e "${RED}   Please install Python 3.8 or higher${NC}"
    exit 1
fi

echo -e "${GREEN}🐍 Using Python ${PYTHON_VERSION}${NC}"

# Check if virtual environment should be activated
if [[ -f "$SCRIPT_DIR/venv/bin/activate" ]]; then
    echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
    source "$SCRIPT_DIR/venv/bin/activate"
elif [[ -f "$SCRIPT_DIR/.venv/bin/activate" ]]; then
    echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Check database status
echo -e "${YELLOW}🗄️  Checking database status...${NC}"
cd "$SCRIPT_DIR"
PYTHONPATH=src $PYTHON_CMD -c "
from davidbot.database import get_database_info
info = get_database_info()
if info['database_exists']:
    print('✅ Database connected:', info['url'])
    if 'tables' in info:
        total_songs = info['tables'].get('songs', 0)
        total_usage = info['tables'].get('song_usage', 0)
        print(f'📊 Songs: {total_songs}, Usage records: {total_usage}')
else:
    print('❌ Database not found - initializing...')
    from davidbot.database import init_database
    init_database()
    print('✅ Database initialized')
" 2>/dev/null || {
    echo -e "${RED}❌ Error: Database check failed${NC}"
    echo -e "${YELLOW}💡 Try running: PYTHONPATH=src python3 -m davidbot.manage init${NC}"
    exit 1
}

# Create the startup Python script
echo -e "${YELLOW}🚀 Starting DavidBot...${NC}"
echo ""

# Export token for the Python script
export TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"

# Run DavidBot with error handling
cd "$SCRIPT_DIR"
PYTHONPATH=src $PYTHON_CMD -c "
import os
import sys
import signal
import asyncio
import logging
from datetime import datetime
from davidbot.main import main as davidbot_main

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('DavidBot')

# Global variable to handle shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    print('\n🛑 Shutdown requested...')
    shutdown_requested = True

# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    global shutdown_requested
    
    print('🤖 DavidBot v2.0 - Enhanced Worship Song Recommendation Bot')
    print('=' * 65)
    print(f'🚀 Starting at: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print('🧠 Enhanced with Mistral LLM natural language processing')
    print('🏷️  Updated tag system with 150+ worship themes')
    print('💬 Natural queries: \"upbeat songs for celebration\"')
    print('⛪ Ministry context: \"slow songs for altar call\"')
    print('📊 Graceful fallback ensures 100% uptime')
    print('🛑 Press Ctrl+C to stop')
    print('=' * 65)
    
    try:
        # Use the enhanced main function which handles Ollama detection
        await davidbot_main()
        
    except KeyboardInterrupt:
        print('\n🛑 Received shutdown signal')
    except Exception as e:
        logger.error(f'Fatal error: {e}')
        sys.exit(1)
    finally:
        print('👋 DavidBot stopped')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n👋 DavidBot stopped')
        sys.exit(0)
" || {
    echo -e "${RED}❌ Error: DavidBot failed to start${NC}"
    exit 1
}