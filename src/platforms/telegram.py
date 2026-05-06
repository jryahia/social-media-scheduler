"""
Telegram platform handler.
"""
from typing import Optional, Dict, Any

from .base import BasePlatform


class TelegramPlatform(BasePlatform):
    """Handler for Telegram platform."""

    @property
    def name(self) -> str:
        return "Telegram"

    def post(self, content: str, media_path: Optional[str] = None) -> bool:
        """Simulate posting to Telegram."""
        preview = content[:50].replace("\n", " ")
        media_info = f" with media: {media_path}" if media_path else ""
        print(f"TELEGRAM: Sending message: {preview}...{media_info} [SIMULATED]")
        return True

    def validate_credentials(self) -> bool:
        """Simulate credential validation."""
        print("TELEGRAM: Bot token validated [SIMULATED]")
        return True

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Return mock engagement data."""
        import random
        return {
            "likes": random.randint(5, 200),
            "retweets": 0,
            "replies": random.randint(0, 30),
            "impressions": random.randint(100, 5000),
        }
