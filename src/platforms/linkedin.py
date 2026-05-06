"""
LinkedIn platform handler.
"""
from typing import Optional, Dict, Any

from .base import BasePlatform


class LinkedInPlatform(BasePlatform):
    """Handler for LinkedIn platform."""

    @property
    def name(self) -> str:
        return "LinkedIn"

    def post(self, content: str, media_path: Optional[str] = None) -> bool:
        """Simulate posting to LinkedIn."""
        preview = content[:50].replace("\n", " ")
        media_info = f" with media: {media_path}" if media_path else ""
        print(f"LINKEDIN: Publishing article: {preview}...{media_info} [SIMULATED]")
        return True

    def validate_credentials(self) -> bool:
        """Simulate credential validation."""
        print("LINKEDIN: OAuth token validated [SIMULATED]")
        return True

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Return mock engagement data."""
        import random
        return {
            "likes": random.randint(5, 200),
            "retweets": random.randint(0, 20),
            "replies": random.randint(0, 30),
            "impressions": random.randint(200, 5000),
        }
