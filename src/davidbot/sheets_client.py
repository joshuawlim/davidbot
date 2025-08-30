"""Google Sheets client with async logging and retries."""

import asyncio
import logging
from typing import Optional
from .models import MessageLog, FeedbackEvent


logger = logging.getLogger(__name__)


class SheetsClient:
    """Client for logging to Google Sheets with error handling."""
    
    def __init__(self, fail_gracefully: bool = True):
        """Initialize sheets client."""
        self.fail_gracefully = fail_gracefully
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    async def log_message(self, message_log: MessageLog) -> bool:
        """Log message interaction to MessageLog sheet."""
        try:
            # Simulate async sheets API call
            await self._make_sheets_request("MessageLog", {
                "user_id": message_log.user_id,
                "message_type": message_log.message_type,
                "message_content": message_log.message_content,
                "response_content": message_log.response_content,
                "timestamp": message_log.timestamp.isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
            if not self.fail_gracefully:
                raise
            return False
    
    async def log_feedback(self, feedback_event: FeedbackEvent) -> bool:
        """Log feedback event to Google Sheets."""
        try:
            # Simulate async sheets API call
            await self._make_sheets_request("FeedbackLog", {
                "user_id": feedback_event.user_id,
                "song_position": feedback_event.song_position,
                "feedback_type": feedback_event.feedback_type,
                "timestamp": feedback_event.timestamp.isoformat(),
                "song_title": feedback_event.song_title
            })
            return True
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
            if not self.fail_gracefully:
                raise
            return False
    
    async def _make_sheets_request(self, sheet_name: str, data: dict) -> None:
        """Make request to Google Sheets API with retries.""" 
        for attempt in range(self.max_retries):
            try:
                # Simulate API call delay
                await asyncio.sleep(0.01)  # Minimal delay for simulation
                
                # This is where real Google Sheets API call would go
                # For now, just simulate success or failure based on test setup
                logger.info(f"Logged to {sheet_name}: {data}")
                return
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Sheets API attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All {self.max_retries} attempts to log to sheets failed: {e}")
                    raise