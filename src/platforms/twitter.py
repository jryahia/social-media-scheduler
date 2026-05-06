"""
Twitter/X platform handler.
"""
from typing import Optional, Dict, Any

from .base import BasePlatform


class TwitterPlatform(BasePlatform):
    """Handler for Twitter/X platform."""

    @property
    def name(self) -> str:
        return "Twitter / X"

    def post(self, content: str, media_path: Optional[str] = None) -> bool:
        """Simulate posting to Twitter."""
        preview = content[:50].replace("\n", " ")
        media_info = f" with media: {media_path}" if media_path else ""
        print(f"TWITTER: Posting: {preview}...{media_info} [SIMULATED]")
        return True

    def validate_credentials(self) -> bool:
        """Simulate credential validation."""
        print("TWITTER: Credentials validated [SIMULATED]")
        return True

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Return mock engagement data."""
        import random
        return {
            "likes": random.randint(10, 500),
            "retweets": random.randint(2, 100),
            "replies": random.randint(1, 50),
            "impressions": random.randint(500, 10000),
        }
