"""
TikTok platform handler.
"""
from typing import Optional, Dict, Any

from .base import BasePlatform


class TikTokPlatform(BasePlatform):
    """Handler for TikTok platform."""

    @property
    def name(self) -> str:
        return "TikTok"

    def post(self, content: str, media_path: Optional[str] = None) -> bool:
        """Simulate posting to TikTok."""
        preview = content[:50].replace("\n", " ")
        media_info = f" with media: {media_path}" if media_path else ""
        print(f"TIKTOK: Uploading video: {preview}...{media_info} [SIMULATED]")
        return True

    def validate_credentials(self) -> bool:
        """Simulate credential validation."""
        print("TIKTOK: API credentials validated [SIMULATED]")
        return True

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Return mock engagement data."""
        import random
        return {
            "likes": random.randint(50, 5000),
            "retweets": 0,
            "replies": random.randint(5, 300),
            "impressions": random.randint(1000, 100000),
        }
