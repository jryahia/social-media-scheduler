"""
Data models for Social Media Scheduler Pro.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Platform(str, Enum):
    TWITTER = "twitter"
    TELEGRAM = "telegram"
    REDDIT = "reddit"
    DISCORD = "discord"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"


class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    POSTING = "posting"
    POSTED = "posted"
    FAILED = "failed"


@dataclass
class ScheduledPost:
    """Represents a post scheduled for a social platform."""
    id: int = 0
    platform: Platform = Platform.TWITTER
    content: str = ""
    media_path: Optional[str] = None
    scheduled_at: Optional[str] = None  # ISO datetime
    status: PostStatus = PostStatus.DRAFT
    created_at: str = ""
    posted_at: Optional[str] = None
    thread_posts: List[str] = field(default_factory=list)
    recurring: Optional[str] = None  # cron expression
    engagement: dict = field(default_factory=dict)
    error_message: Optional[str] = None

    @property
    def preview(self) -> str:
        """Get a shortened preview of content."""
        text = self.content[:80]
        if len(self.content) > 80:
            text += "..."
        return text

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "platform": self.platform.value,
            "content": self.content,
            "media_path": self.media_path,
            "scheduled_at": self.scheduled_at,
            "status": self.status.value,
            "created_at": self.created_at,
            "posted_at": self.posted_at,
            "thread_posts": ",".join(self.thread_posts),
            "recurring": self.recurring,
            "engagement": str(self.engagement),
            "error_message": self.error_message,
        }


@dataclass
class PlatformAccount:
    """Represents a connected social media account."""
    id: int = 0
    platform: Platform = Platform.TWITTER
    name: str = ""
    credentials: dict = field(default_factory=dict)
    is_active: bool = True
    added_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "platform": self.platform.value,
            "name": self.name,
            "credentials": str(self.credentials),
            "is_active": int(self.is_active),
            "added_at": self.added_at,
        }
