"""
Platform handler factory — maps Platform enum to handler class.
"""
from typing import Dict, Optional

from ..models import Platform

from .base import BasePlatform
from .twitter import TwitterPlatform
from .telegram import TelegramPlatform
from .reddit import RedditPlatform
from .discord import DiscordPlatform
from .instagram import InstagramPlatform
from .linkedin import LinkedInPlatform
from .tiktok import TikTokPlatform


# Registry of all platform handlers
_PLATFORM_REGISTRY: Dict[Platform, type] = {
    Platform.TWITTER: TwitterPlatform,
    Platform.TELEGRAM: TelegramPlatform,
    Platform.REDDIT: RedditPlatform,
    Platform.DISCORD: DiscordPlatform,
    Platform.INSTAGRAM: InstagramPlatform,
    Platform.LINKEDIN: LinkedInPlatform,
    Platform.TIKTOK: TikTokPlatform,
}


def get_platform_handler(platform: Platform) -> BasePlatform:
    """Get the handler instance for a given platform."""
    handler_cls = _PLATFORM_REGISTRY.get(platform)
    if handler_cls is None:
        raise ValueError(f"Unknown platform: {platform}")
    return handler_cls()


def get_all_platforms() -> list:
    """Get list of all platform enum values."""
    return list(Platform)
