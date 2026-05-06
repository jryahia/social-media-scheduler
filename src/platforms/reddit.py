"""
Reddit platform handler.
"""
from typing import Optional, Dict, Any

from .base import BasePlatform


class RedditPlatform(BasePlatform):
    """Handler for Reddit platform."""

    @property
    def name(self) -> str:
        return "Reddit"

    def post(self, content: str, media_path: Optional[str] = None) -> bool:
        """Simulate posting to Reddit."""
        preview = content[:50].replace("\n", " ")
        media_info = f" with media: {media_path}" if media_path else ""
        print(f"REDDIT: Submitting post: {preview}...{media_info} [SIMULATED]")
        return True

    def validate_credentials(self) -> bool:
        """Simulate credential validation."""
        print("REDDIT: OAuth credentials validated [SIMULATED]")
        return True

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Return mock engagement data."""
        import random
        return {
            "likes": random.randint(5, 300),
            "retweets": 0,
            "replies": random.randint(1, 80),
            "impressions": random.randint(200, 8000),
        }
