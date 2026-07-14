"""
Twitter/X platform handler.
"""
import logging
from typing import Optional, Dict, Any

from .base import BasePlatform

logger = logging.getLogger(__name__)


class TwitterPlatform(BasePlatform):
    """Handler for Twitter/X platform."""

    @property
    def name(self) -> str:
        return "Twitter"

    def post(self, content: str, media_path: Optional[str] = None) -> bool:
        """Simulate posting to Twitter."""
        preview = content[:50].replace("\n", " ")
        media_info = f" with media: {media_path}" if media_path else ""
        logger.info(f"TWITTER: Posting: {preview}...{media_info} [SIMULATED]")
        return True

    def validate_credentials(self) -> bool:
        """Simulate credential validation."""
        logger.info("TWITTER: Credentials validated [SIMULATED]")
        return True

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Return mock engagement data."""
        import random
        return {
            "likes": random.randint(0, 100),
            "retweets": random.randint(0, 30),
            "replies": random.randint(0, 20),
            "impressions": random.randint(100, 5000),
        }
