"""
UI components for Social Media Scheduler Pro.
"""
import flet as ft
from typing import Callable, List, Optional

from ..models import ScheduledPost, PostStatus, Platform
from ..utils import (
    get_platform_color, get_platform_emoji, get_platform_icon,
    get_status_color, format_time_ago,
)


# --- Theme ---
class Theme:
    BG_DARK = "#0D1117"
    BG_CARD = "#161B22"
    BG_INPUT = "#21262D"
    BG_HOVER = "#1C2128"
    TEXT_PRIMARY = "#F0F6FC"
    TEXT_SECONDARY = "#8B949E"
    TEXT_MUTED = "#484F58"
    ACCENT_GREEN = "#00FF88"
    ACCENT_RED = "#FF4444"
    ACCENT_AMBER = "#FFB347"
    ACCENT_BLUE = "#58A6FF"
    ACCENT_PURPLE = "#BB86FC"
    BORDER = "#30363D"


def build_platform_badge(platform: Platform) -> ft.Container:
    """Build a platform badge with emoji and color."""
    color = get_platform_color(platform)
    emoji = get_platform_emoji(platform)
    return ft.Container(
        content=ft.Row([
            ft.Text(emoji, size=12),
            ft.Text(platform.value.capitalize(), size=10, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY),
        ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        bgcolor=color + "22",
        border_radius=4,
    )


def build_status_badge(status: PostStatus) -> ft.Container:
    """Build a status badge."""
    color = get_status_color(status)
    return ft.Container(
        content=ft.Text(status.value.upper(), size=9, weight=ft.FontWeight.W_600, color=color),
        padding=ft.padding.symmetric(horizontal=6, vertical=2),
        bgcolor=color + "22",
        border_radius=4,
    )


def build_post_card(post: ScheduledPost, on_click: Optional[Callable] = None,
                    on_delete: Optional[Callable] = None) -> ft.Container:
    """Build a post card for display in lists."""
    platform_color = get_platform_color(post.platform)
    status_color = get_status_color(post.status)

    actions_row = []
    if on_delete and post.status in (PostStatus.DRAFT, PostStatus.SCHEDULED):
        actions_row.append(
            ft.IconButton(
                icon=ft.icons.DELETE_OUTLINE,
                icon_size=16,
                icon_color=Theme.TEXT_MUTED,
                on_click=lambda _: on_delete(post),
                tooltip="Delete post",
            )
        )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                # Platform badge
                build_platform_badge(post.platform),
                # Status badge
                build_status_badge(post.status),
                ft.Container(expand=True),
                ft.Text(f"#{post.id}", size=10, color=Theme.TEXT_MUTED),
            ]),
            # Content preview
            ft.Text(post.preview, size=12, color=Theme.TEXT_PRIMARY, max_lines=2),
            # Meta row
            ft.Row([
                ft.Icon(ft.icons.SCHEDULE, size=12, color=Theme.TEXT_MUTED),
                ft.Text(
                    post.scheduled_at.replace("T", " ") if post.scheduled_at else "No schedule",
                    size=10, color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(expand=True),
                ft.Text(
                    f"Posted: {format_time_ago(post.posted_at)}" if post.posted_at else "",
                    size=10, color=Theme.TEXT_MUTED,
                ),
            ]),
            # Engagement stats for posted items
            ft.Row([
                ft.Text(f"❤️ {post.engagement.get('likes', 0)}", size=10, color=Theme.TEXT_SECONDARY),
                ft.Text(f"🔁 {post.engagement.get('retweets', 0)}", size=10, color=Theme.TEXT_SECONDARY),
                ft.Text(f"💬 {post.engagement.get('replies', 0)}", size=10, color=Theme.TEXT_SECONDARY),
                ft.Text(f"👁 {post.engagement.get('impressions', 0)}", size=10, color=Theme.TEXT_SECONDARY),
            ], spacing=8) if post.status == PostStatus.POSTED else ft.Container(),
            # Error message
            ft.Text(post.error_message or "", size=10, color=Theme.ACCENT_RED) if post.error_message else ft.Container(),
        ], spacing=4),
        padding=10,
        bgcolor=Theme.BG_CARD,
        border=ft.border.all(1, Theme.BORDER),
        border_radius=8,
        ink=True,
        on_click=lambda _: on_click(post) if on_click else None,
    )


def build_schedule_form(on_submit: Callable) -> ft.Container:
    """Build the schedule post form."""
    # Platform dropdown
    platform_dropdown = ft.Dropdown(
        label="Platform",
        label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
        options=[
            ft.dropdown.Option("twitter", "🐦 Twitter / X"),
            ft.dropdown.Option("telegram", "✈️ Telegram"),
            ft.dropdown.Option("reddit", "🤖 Reddit"),
            ft.dropdown.Option("discord", "🎮 Discord"),
            ft.dropdown.Option("instagram", "📸 Instagram"),
            ft.dropdown.Option("linkedin", "💼 LinkedIn"),
            ft.dropdown.Option("tiktok", "🎵 TikTok"),
        ],
        value="twitter",
        width=200,
        text_size=13,
        dense=True,
        bgcolor=Theme.BG_INPUT,
        color=Theme.TEXT_PRIMARY,
        border_color=Theme.BORDER,
    )

    # Content text area
    content_field = ft.TextField(
        label="Post Content",
        label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
        hint_text="What do you want to share?",
        multiline=True,
        min_lines=3,
        max_lines=6,
        text_size=13,
        bgcolor=Theme.BG_INPUT,
        color=Theme.TEXT_PRIMARY,
        border_color=Theme.BORDER,
        cursor_color=Theme.ACCENT_BLUE,
    )

    # Media path
    media_field = ft.TextField(
        label="Media Path (optional)",
        label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
        hint_text="/path/to/image.png",
        text_size=12,
        dense=True,
        bgcolor=Theme.BG_INPUT,
        color=Theme.TEXT_PRIMARY,
        border_color=Theme.BORDER,
    )

    # Date & Time inputs
    date_field = ft.TextField(
        label="Date (YYYY-MM-DD)",
        label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
        hint_text="2026-05-06",
        text_size=12,
        width=160,
        dense=True,
        bgcolor=Theme.BG_INPUT,
        color=Theme.TEXT_PRIMARY,
        border_color=Theme.BORDER,
    )
    time_field = ft.TextField(
        label="Time (HH:MM)",
        label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
        hint_text="14:30",
        text_size=12,
        width=120,
        dense=True,
        bgcolor=Theme.BG_INPUT,
        color=Theme.TEXT_PRIMARY,
        border_color=Theme.BORDER,
    )

    # Recurring / Thread toggles
    recurring_field = ft.TextField(
        label="Cron (optional)",
        label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
        hint_text="0 9 * * 1-5 (weekdays at 9am)",
        text_size=12,
        dense=True,
        width=250,
        bgcolor=Theme.BG_INPUT,
        color=Theme.TEXT_PRIMARY,
        border_color=Theme.BORDER,
    )

    thread_field = ft.TextField(
        label="Thread posts (one per line)",
        label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
        hint_text="Post 2 content...\nPost 3 content...",
        multiline=True,
        min_lines=2,
        max_lines=4,
        text_size=12,
        width=300,
        bgcolor=Theme.BG_INPUT,
        color=Theme.TEXT_PRIMARY,
        border_color=Theme.BORDER,
    )

    status_text = ft.Text("", size=11, color=Theme.TEXT_SECONDARY)

    def on_schedule_click(e):
        """Handle schedule form submission."""
        platform = platform_dropdown.value
        content = content_field.value.strip()
        if not content:
            status_text.value = "❌ Content is required"
            status_text.color = Theme.ACCENT_RED
            status_text.update()
            return

        date_val = date_field.value.strip()
        time_val = time_field.value.strip()
        scheduled_at = None
        if date_val and time_val:
            scheduled_at = f"{date_val}T{time_val}:00"

        on_submit({
            "platform": platform,
            "content": content,
            "media_path": media_field.value.strip() or None,
            "scheduled_at": scheduled_at,
            "recurring": recurring_field.value.strip() or None,
            "thread_posts": [t.strip() for t in thread_field.value.split("\n") if t.strip()] if thread_field.value else [],
        })

        # Clear form
        content_field.value = ""
        media_field.value = ""
        date_field.value = ""
        time_field.value = ""
        recurring_field.value = ""
        thread_field.value = ""
        status_text.value = "✅ Post scheduled!"
        status_text.color = Theme.ACCENT_GREEN
        status_text.update()

    return ft.Container(
        content=ft.Column([
            ft.Text("📝 Schedule a New Post", weight=ft.FontWeight.BOLD, size=16, color=Theme.TEXT_PRIMARY),
            ft.Divider(color=Theme.BORDER, height=1),
            # Platform + Content
            ft.Row([
                platform_dropdown,
                ft.Container(expand=True),
            ]),
            content_field,
            # Media + Recurring
            ft.Row([
                media_field,
                recurring_field,
            ], wrap=True, spacing=8),
            # Date/Time row
            ft.Row([
                date_field,
                time_field,
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "📅 Schedule Post",
                    on_click=on_schedule_click,
                    bgcolor=Theme.ACCENT_GREEN + "22",
                    color=Theme.ACCENT_GREEN,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
            ]),
            # Thread
            ft.Row([
                ft.Column([
                    ft.Text("Thread (optional):", size=11, color=Theme.TEXT_SECONDARY),
                    thread_field,
                ], expand=True),
            ]),
            status_text,
        ], spacing=8),
        padding=14,
        bgcolor=Theme.BG_CARD,
        border=ft.border.all(1, Theme.BORDER),
        border_radius=8,
    )


def build_analytics_card(label: str, value: str, icon: str) -> ft.Container:
    """Build an analytics summary card."""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(icon, size=20, color=Theme.ACCENT_BLUE),
                ft.Text(value, weight=ft.FontWeight.BOLD, size=22, color=Theme.TEXT_PRIMARY),
            ]),
            ft.Text(label, size=11, color=Theme.TEXT_SECONDARY),
        ], spacing=4),
        padding=12,
        bgcolor=Theme.BG_CARD,
        border=ft.border.all(1, Theme.BORDER),
        border_radius=8,
        expand=True,
    )


def build_status_bar(text: str) -> ft.Container:
    """Build a status bar at the bottom."""
    return ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.CIRCLE, size=8, color=Theme.ACCENT_GREEN),
            ft.Text(text, size=10, color=Theme.TEXT_SECONDARY),
        ], spacing=4),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=Theme.BG_CARD,
        border=ft.border.only(top=ft.BorderSide(1, Theme.BORDER)),
    )
