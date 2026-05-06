"""
Utility functions for Social Media Scheduler Pro.
"""
import json
import os
from datetime import datetime
from typing import Optional

from .models import Platform

# --- Paths ---
PROJECT_DIR = os.path.expanduser("~/.hermes/profiles/codex/workspace/projects/social_scheduler")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "scheduler.db")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")

# --- Default Config ---
DEFAULT_CONFIG = {
    "scheduler_interval": 30,
    "dark_mode": True,
    "notifications_enabled": True,
}


def load_config() -> dict:
    """Load configuration from JSON file."""
    config = DEFAULT_CONFIG.copy()
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                saved = json.load(f)
                config.update(saved)
    except Exception:
        pass
    return config


def save_config(config: dict):
    """Save configuration to JSON file."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def format_time_ago(dt_str: str) -> str:
    """Convert ISO datetime string to human-readable 'time ago'."""
    if not dt_str:
        return "never"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo if dt.tzinfo else None)
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 0:
            return "soon"
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except Exception:
        return dt_str


def get_platform_color(platform: Platform) -> str:
    """Get accent color for a social platform."""
    colors = {
        Platform.TWITTER: "#1DA1F2",
        Platform.TELEGRAM: "#0088CC",
        Platform.REDDIT: "#FF4500",
        Platform.DISCORD: "#5865F2",
        Platform.INSTAGRAM: "#E4405F",
        Platform.LINKEDIN: "#0A66C2",
        Platform.TIKTOK: "#000000",
    }
    return colors.get(platform, "#888888")


def get_platform_icon(platform: Platform) -> str:
    """Get icon name for a social platform (Material icons)."""
    icons = {
        Platform.TWITTER: "alternate_email",
        Platform.TELEGRAM: "send",
        Platform.REDDIT: "forum",
        Platform.DISCORD: "headset_mic",
        Platform.INSTAGRAM: "camera_alt",
        Platform.LINKEDIN: "work",
        Platform.TIKTOK: "music_note",
    }
    return icons.get(platform, "share")


def get_platform_emoji(platform: Platform) -> str:
    """Get emoji for a social platform."""
    emojis = {
        Platform.TWITTER: "🐦",
        Platform.TELEGRAM: "✈️",
        Platform.REDDIT: "🤖",
        Platform.DISCORD: "🎮",
        Platform.INSTAGRAM: "📸",
        Platform.LINKEDIN: "💼",
        Platform.TIKTOK: "🎵",
    }
    return emojis.get(platform, "📱")


def get_status_color(status) -> str:
    """Get color for a post status."""
    from .models import PostStatus
    colors = {
        PostStatus.DRAFT: "#8B949E",
        PostStatus.SCHEDULED: "#58A6FF",
        PostStatus.POSTING: "#FFB347",
        PostStatus.POSTED: "#00FF88",
        PostStatus.FAILED: "#FF4444",
    }
    return colors.get(status, "#8B949E")
