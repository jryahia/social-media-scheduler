"""
Base platform class for all social media integrations.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any


class BasePlatform(ABC):
    """Abstract base class for social media platform handlers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable platform name."""
        ...

    @abstractmethod
    def post(self, content: str, media_path: Optional[str] = None) -> bool:
        """Post content to the platform. Returns True on success."""
        ...

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate that the stored credentials work."""
        ...

    @abstractmethod
    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Get engagement metrics for a post."""
        ...

    def format_content(self, content: str) -> str:
        """Format content per platform requirements. Override in subclass."""
        return content.strip()
