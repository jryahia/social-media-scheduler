"""
Discord platform handler.
"""
import logging
from typing import Optional, Dict, Any

from .base import BasePlatform

logger = logging.getLogger(__name__)


class DiscordPlatform(BasePlatform):
    """Handler for Discord platform."""

    @property
    def name(self) -> str:
        return "Discord"

    def post(self, content: str, media_path: Optional[str] = None) -> bool:
        """Simulate posting to Discord."""
        preview = content[:50].replace("\n", " ")
        media_info = f" with media: {media_path}" if media_path else ""
        logger.info(f"DISCORD: Sending message to channel: {preview}...{media_info} [SIMULATED]")
        return True

    def validate_credentials(self) -> bool:
        """Simulate credential validation."""
        logger.info("DISCORD: Bot token validated [SIMULATED]")
        return True

    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Return mock engagement data."""
        import random
        return {
            "likes": 0,
            "retweets": 0,
            "replies": random.randint(0, 40),
            "impressions": random.randint(50, 2000),
        }
