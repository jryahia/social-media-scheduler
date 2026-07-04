"""
Main Flet UI for Social Media Scheduler Pro — 4-tab dark-themed interface.
"""
import threading
from datetime import datetime
from typing import List, Optional

import flet as ft

from ..models import ScheduledPost, PostStatus, Platform, PlatformAccount
from ..database import (
    init_db, save_post, get_posts, get_upcoming_posts, update_post_status,
    delete_post, save_account, get_accounts, delete_account, get_drafts,
    save_draft, get_analytics_summary, clear_post_history,
)
from ..scheduler_engine import SchedulerEngine
from ..utils import (
    load_config, save_config, format_time_ago, get_platform_color,
    get_platform_emoji, get_status_color,
)
from ..xquik import build_xquik_source_notes
from .components import (
    Theme, build_post_card, build_platform_badge, build_schedule_form,
    build_analytics_card, build_status_bar,
)


class SocialSchedulerApp:
    """Main application controller for Social Media Scheduler Pro."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.config = load_config()
        self.scheduler = SchedulerEngine(interval=self.config.get("scheduler_interval", 30))

        # State
        self._upcoming_posts: List[ScheduledPost] = []
        self._all_posts: List[ScheduledPost] = []
        self._accounts: List[PlatformAccount] = []
        self._analytics: dict = {}
        self._drafts: List[dict] = []

        # UI Ref holders
        self.upcoming_list_view = ft.ListView(expand=True, spacing=6, padding=8)
        self.pending_list_view = ft.ListView(expand=True, spacing=6, padding=8)
        self.posting_list_view = ft.ListView(expand=True, spacing=6, padding=8)
        self.history_list_view = ft.ListView(expand=True, spacing=6, padding=8)
        self.analytics_cards_row = ft.Row(spacing=8, wrap=True)
        self.activity_list_view = ft.ListView(expand=True, spacing=4, padding=8)
        self.platform_breakdown_view = ft.Column(spacing=4)
        self.accounts_list_view = ft.ListView(expand=True, spacing=6, padding=8)
        self.status_text = ft.Text("Ready", size=10, color=Theme.TEXT_SECONDARY)
        self.scheduler_status = ft.Text("● Stopped", size=11, color=Theme.ACCENT_RED)

        self._setup_page()
        init_db()

        # Register scheduler callbacks
        self.scheduler.on("on_post_start", self._on_post_start)
        self.scheduler.on("on_post_success", self._on_post_success)
        self.scheduler.on("on_post_fail", self._on_post_fail)

        # Start scheduler
        self.scheduler.start()
        self._update_scheduler_status()

        # Initial load
        self._refresh_all()

    def _setup_page(self):
        """Configure the page."""
        self.page.title = "Social Media Scheduler Pro"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = Theme.BG_DARK
        self.page.padding = 0
        self.page.window.width = 1200
        self.page.window.height = 800
        self.page.window.min_width = 900
        self.page.window.min_height = 650

        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=Theme.ACCENT_GREEN,
                on_primary=Theme.BG_DARK,
                surface=Theme.BG_CARD,
                on_surface=Theme.TEXT_PRIMARY,
                background=Theme.BG_DARK,
                on_background=Theme.TEXT_PRIMARY,
            ),
        )

        # Build UI
        self.page.add(self._build_ui())
        self.page.update()

    def _build_ui(self) -> ft.Container:
        """Build the complete UI with tabs."""
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="  📅 Schedule  ",
                    content=self._build_schedule_tab(),
                ),
                ft.Tab(
                    text="  📋 Queue  ",
                    content=self._build_queue_tab(),
                ),
                ft.Tab(
                    text="  📊 Analytics  ",
                    content=self._build_analytics_tab(),
                ),
                ft.Tab(
                    text="  ⚙ Settings  ",
                    content=self._build_settings_tab(),
                ),
            ],
            label_color=Theme.TEXT_PRIMARY,
            unselected_label_color=Theme.TEXT_MUTED,
            indicator_color=Theme.ACCENT_GREEN,
        )

        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.SCHEDULE_SEND, color=Theme.ACCENT_GREEN, size=28),
                        ft.Text("Social Media Scheduler Pro", weight=ft.FontWeight.BOLD, size=20, color=Theme.TEXT_PRIMARY),
                        ft.Container(expand=True),
                        self.scheduler_status,
                    ]),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                    bgcolor=Theme.BG_DARK,
                    border=ft.Border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
                ),
                # Tabs
                ft.Container(content=tabs, expand=True),
                # Status bar
                build_status_bar("Ready • Schedule posts across 7 platforms • Scheduler active"),
            ], spacing=0),
            expand=True,
            bgcolor=Theme.BG_DARK,
        )

    # ===== Tab 1: Schedule =====

    def _build_schedule_tab(self) -> ft.Container:
        """Build the Schedule tab with form and upcoming posts."""
        self.upcoming_header = ft.Text("Upcoming Posts", weight=ft.FontWeight.BOLD, size=14, color=Theme.TEXT_PRIMARY)

        return ft.Container(
            content=ft.Column([
                # Schedule form
                build_schedule_form(on_submit=self._on_schedule_submit),
                # Divider
                ft.Divider(color=Theme.BORDER, height=1),
                # Upcoming posts list
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            self.upcoming_header,
                            ft.Container(expand=True),
                            ft.TextButton(
                                "🔄 Refresh",
                                on_click=self._on_refresh_upcoming,
                                style=ft.ButtonStyle(color=Theme.ACCENT_BLUE, text_style=ft.TextStyle(size=11)),
                            ),
                        ]),
                        self.upcoming_list_view,
                    ]),
                    expand=True,
                ),
            ], spacing=0),
            expand=True,
        )

    def _on_schedule_submit(self, data: dict):
        """Handle schedule form submission."""
        try:
            platform = Platform(data["platform"])
            now = datetime.now().isoformat()
            thread_posts = list(data.get("thread_posts", []))
            xquik_topic = data.get("xquik_topic")
            xquik_notes = build_xquik_source_notes(xquik_topic) if xquik_topic else []
            thread_posts.extend(xquik_notes)

            post = ScheduledPost(
                platform=platform,
                content=data["content"],
                media_path=data.get("media_path"),
                scheduled_at=data.get("scheduled_at"),
                status=PostStatus.SCHEDULED if data.get("scheduled_at") else PostStatus.DRAFT,
                created_at=now,
                thread_posts=thread_posts,
                recurring=data.get("recurring"),
            )

            save_post(post)
            self.scheduler.schedule_post(post)
            self._refresh_upcoming()
            suffix = f" with {len(xquik_notes)} Xquik sources" if xquik_notes else ""
            self._update_status(f"✅ {platform.value.capitalize()} post scheduled{suffix}!")
        except Exception as e:
            self._update_status(f"❌ Error: {str(e)[:60]}", Theme.ACCENT_RED)
            print(f"[App] Schedule error: {e}")

    def _on_refresh_upcoming(self, e=None):
        self._refresh_upcoming()

    def _refresh_upcoming(self):
        """Refresh the upcoming posts list."""
        self.upcoming_list_view.controls.clear()
        posts = get_upcoming_posts(limit=20)

        if not posts:
            self.upcoming_list_view.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.POST_ADD, size=48, color=Theme.TEXT_MUTED),
                        ft.Text("No upcoming posts", size=14, color=Theme.TEXT_SECONDARY),
                        ft.Text("Use the form above to schedule your first post!", size=11, color=Theme.TEXT_MUTED),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    expand=True,
                )
            )
        else:
            for post in posts:
                card = build_post_card(
                    post,
                    on_click=self._on_post_click,
                    on_delete=self._on_delete_post,
                )
                self.upcoming_list_view.controls.append(card)

        self.upcoming_header.value = f"Upcoming Posts ({len(posts)})"
        self.upcoming_list_view.update()
        self.upcoming_header.update()

    # ===== Tab 2: Queue =====

    def _build_queue_tab(self) -> ft.Container:
        """Build the Queue tab with pending, posting, and history sections."""
        self.pending_header = ft.Text("Pending", weight=ft.FontWeight.BOLD, size=13, color=Theme.TEXT_PRIMARY)
        self.posting_header = ft.Text("Posting", weight=ft.FontWeight.BOLD, size=13, color=Theme.ACCENT_AMBER)
        self.history_header = ft.Text("History", weight=ft.FontWeight.BOLD, size=13, color=Theme.TEXT_PRIMARY)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.TextButton("🔄 Refresh All", on_click=self._on_refresh_queue, style=ft.ButtonStyle(color=Theme.ACCENT_BLUE, text_style=ft.TextStyle(size=11))),
                ]),
                # Pending section
                ft.Container(
                    content=ft.Column([
                        self.pending_header,
                        ft.Container(content=self.pending_list_view, height=200),
                    ]),
                    padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                ),
                ft.Divider(color=Theme.BORDER, height=1),
                # Posting section
                ft.Container(
                    content=ft.Column([
                        self.posting_header,
                        ft.Container(content=self.posting_list_view, height=100),
                    ]),
                    padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                ),
                ft.Divider(color=Theme.BORDER, height=1),
                # History section
                ft.Container(
                    content=ft.Column([
                        self.history_header,
                        ft.Container(content=self.history_list_view, expand=True),
                    ]),
                    expand=True,
                    padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                ),
            ], spacing=4),
            expand=True,
        )

    def _on_refresh_queue(self, e=None):
        self._refresh_queue()

    def _refresh_queue(self):
        """Refresh all queue sections."""
        # Pending
        self.pending_list_view.controls.clear()
        pending = get_posts(status_filter=PostStatus.SCHEDULED.value)
        for post in pending:
            card = build_post_card(post, on_delete=self._on_delete_post)
            self.pending_list_view.controls.append(card)
        if not pending:
            self.pending_list_view.controls.append(
                ft.Text("No pending posts", size=11, color=Theme.TEXT_MUTED)
            )
        self.pending_header.value = f"📋 Pending ({len(pending)})"

        # Posting
        self.posting_list_view.controls.clear()
        posting = get_posts(status_filter=PostStatus.POSTING.value)
        for post in posting:
            card = build_post_card(post)
            self.posting_list_view.controls.append(card)
        if not posting:
            self.posting_list_view.controls.append(
                ft.Text("Nothing currently posting", size=11, color=Theme.TEXT_MUTED)
            )
        self.posting_header.value = f"🔄 Posting ({len(posting)})"

        # History (posted + failed)
        self.history_list_view.controls.clear()
        posted = get_posts(status_filter=PostStatus.POSTED.value)
        failed = get_posts(status_filter=PostStatus.FAILED.value)
        all_history = posted + failed
        all_history.sort(key=lambda p: p.posted_at or p.created_at or "", reverse=True)
        for post in all_history[:50]:
            card = build_post_card(post, on_click=self._on_post_click)
            self.history_list_view.controls.append(card)
        if not all_history:
            self.history_list_view.controls.append(
                ft.Text("No post history yet", size=11, color=Theme.TEXT_MUTED)
            )
        self.history_header.value = f"📜 History ({len(all_history)})"

        self.pending_header.update()
        self.posting_header.update()
        self.history_header.update()
        self.pending_list_view.update()
        self.posting_list_view.update()
        self.history_list_view.update()

    # ===== Tab 3: Analytics =====

    def _build_analytics_tab(self) -> ft.Container:
        """Build the Analytics tab."""
        self.activity_header = ft.Text("Recent Activity", weight=ft.FontWeight.BOLD, size=13, color=Theme.TEXT_PRIMARY)
        self.breakdown_header = ft.Text("Per-Platform Breakdown", weight=ft.FontWeight.BOLD, size=13, color=Theme.TEXT_PRIMARY)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📊 Analytics Dashboard", weight=ft.FontWeight.BOLD, size=16, color=Theme.TEXT_PRIMARY),
                    ft.Container(expand=True),
                    ft.TextButton("🔄 Refresh", on_click=self._on_refresh_analytics, style=ft.ButtonStyle(color=Theme.ACCENT_BLUE, text_style=ft.TextStyle(size=11))),
                ]),
                # Summary cards
                self.analytics_cards_row,
                ft.Divider(color=Theme.BORDER, height=1),
                # Activity + Breakdown
                ft.Row([
                    # Recent activity
                    ft.Container(
                        content=ft.Column([
                            self.activity_header,
                            self.activity_list_view,
                        ]),
                        expand=2,
                        padding=4,
                    ),
                    # Platform breakdown
                    ft.Container(
                        content=ft.Column([
                            self.breakdown_header,
                            self.platform_breakdown_view,
                        ]),
                        expand=1,
                        padding=4,
                    ),
                ], expand=True),
            ], spacing=8),
            expand=True,
        )

    def _on_refresh_analytics(self, e=None):
        self._refresh_analytics()

    def _refresh_analytics(self):
        """Refresh analytics data."""
        analytics = get_analytics_summary()

        # Summary cards
        self.analytics_cards_row.controls.clear()
        cards_data = [
            ("Total Posts", str(analytics.get("total_posts", 0)), ft.icons.POST_ADD),
            ("Posted Today", str(analytics.get("posted_today", 0)), ft.icons.TODAY),
            ("Success Rate", f"{analytics.get('success_rate', 0)}%", ft.icons.CHECK_CIRCLE),
            ("Active Platforms", str(analytics.get("active_platforms", 0)), ft.icons.PUBLIC),
        ]
        for label, value, icon in cards_data:
            self.analytics_cards_row.controls.append(
                build_analytics_card(label, value, icon)
            )

        # Recent activity
        self.activity_list_view.controls.clear()
        recent = analytics.get("recent_activity", [])
        for item in recent[:20]:
            platform = item.get("platform", "unknown")
            content = item.get("content", "")[:60]
            posted = item.get("posted_at", "")
            success = item.get("success", 1)
            color = Theme.ACCENT_GREEN if success else Theme.ACCENT_RED
            icon = "✅" if success else "❌"
            self.activity_list_view.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{icon}", size=14),
                        ft.Text(f"[{platform}] {content}", size=11, color=Theme.TEXT_PRIMARY, max_lines=1),
                        ft.Container(expand=True),
                        ft.Text(format_time_ago(posted), size=10, color=Theme.TEXT_MUTED),
                    ]),
                    padding=ft.Padding.symmetric(horizontal=4, vertical=2),
                )
            )
        if not recent:
            self.activity_list_view.controls.append(
                ft.Text("No activity yet", size=11, color=Theme.TEXT_MUTED)
            )
        self.activity_header.value = f"Recent Activity ({len(recent)})"

        # Platform breakdown
        self.platform_breakdown_view.controls.clear()
        per_platform = analytics.get("per_platform", {})
        for plat, count in sorted(per_platform.items(), key=lambda x: x[1], reverse=True):
            try:
                p = Platform(plat)
                emoji = get_platform_emoji(p)
                color = get_platform_color(p)
            except ValueError:
                emoji = "📱"
                color = Theme.TEXT_SECONDARY
            self.platform_breakdown_view.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{emoji} {plat.capitalize()}", size=12, color=color),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(str(count), size=12, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                            bgcolor=color + "22",
                            border_radius=4,
                        ),
                    ]),
                    padding=ft.Padding.symmetric(vertical=3),
                )
            )
        if not per_platform:
            self.platform_breakdown_view.controls.append(
                ft.Text("No posts yet", size=11, color=Theme.TEXT_MUTED)
            )
        self.breakdown_header.value = f"Per-Platform Breakdown ({len(per_platform)})"

        self.analytics_cards_row.update()
        self.activity_header.update()
        self.breakdown_header.update()
        self.activity_list_view.update()
        self.platform_breakdown_view.update()

    # ===== Tab 4: Settings =====

    def _build_settings_tab(self) -> ft.Container:
        """Build the Settings tab."""
        # Scheduler interval
        self.interval_field = ft.TextField(
            label="Scheduler Check Interval (seconds)",
            label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
            value=str(self.config.get("scheduler_interval", 30)),
            text_size=12,
            width=200,
            dense=True,
            bgcolor=Theme.BG_INPUT,
            color=Theme.TEXT_PRIMARY,
            border_color=Theme.BORDER,
        )

        # Add account form
        self.add_platform_dropdown = ft.Dropdown(
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
            width=180,
            text_size=13,
            dense=True,
            bgcolor=Theme.BG_INPUT,
            color=Theme.TEXT_PRIMARY,
            border_color=Theme.BORDER,
        )
        self.add_account_name = ft.TextField(
            label="Account Name",
            label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
            hint_text="My Twitter Account",
            text_size=12,
            width=200,
            dense=True,
            bgcolor=Theme.BG_INPUT,
            color=Theme.TEXT_PRIMARY,
            border_color=Theme.BORDER,
        )
        self.add_account_api_key = ft.TextField(
            label="API Key / Token (placeholder)",
            label_style=ft.TextStyle(size=11, color=Theme.TEXT_MUTED),
            hint_text="Enter your API key",
            text_size=12,
            width=250,
            dense=True,
            bgcolor=Theme.BG_INPUT,
            color=Theme.TEXT_PRIMARY,
            border_color=Theme.BORDER,
        )

        settings_status = ft.Text("", size=11, color=Theme.TEXT_SECONDARY)

        def on_save_settings(e):
            """Save settings."""
            try:
                interval = int(self.interval_field.value)
                if interval < 5:
                    settings_status.value = "❌ Minimum interval is 5 seconds"
                    settings_status.color = Theme.ACCENT_RED
                    settings_status.update()
                    return
                self.config["scheduler_interval"] = interval
                save_config(self.config)
                settings_status.value = "✅ Settings saved! Restart app for interval change."
                settings_status.color = Theme.ACCENT_GREEN
            except ValueError:
                settings_status.value = "❌ Invalid interval value"
                settings_status.color = Theme.ACCENT_RED
            settings_status.update()

        def on_add_account(e):
            """Add a platform account."""
            platform = self.add_platform_dropdown.value
            name = self.add_account_name.value.strip()
            api_key = self.add_account_api_key.value.strip()
            if not name:
                settings_status.value = "❌ Account name is required"
                settings_status.color = Theme.ACCENT_RED
                settings_status.update()
                return
            account = PlatformAccount(
                platform=Platform(platform),
                name=name,
                credentials={"api_key": api_key} if api_key else {},
                is_active=True,
            )
            save_account(account)
            self._refresh_accounts()
            self.add_account_name.value = ""
            self.add_account_api_key.value = ""
            settings_status.value = f"✅ Added {name} ({platform})"
            settings_status.color = Theme.ACCENT_GREEN
            settings_status.update()

        def on_clear_history(e):
            """Clear all post history."""
            clear_post_history()
            self._refresh_all()
            settings_status.value = "✅ History cleared"
            settings_status.color = Theme.ACCENT_GREEN
            settings_status.update()

        def on_export_data(e):
            """Export data (simulated)."""
            settings_status.value = "📦 Data exported to data/export.json (simulated)"
            settings_status.color = Theme.ACCENT_BLUE
            settings_status.update()

        return ft.Container(
            content=ft.Column([
                ft.Text("⚙ Settings", weight=ft.FontWeight.BOLD, size=16, color=Theme.TEXT_PRIMARY),
                ft.Divider(color=Theme.BORDER, height=1),
                # Scheduler section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Scheduler", weight=ft.FontWeight.W_600, size=14, color=Theme.TEXT_SECONDARY),
                        ft.Row([
                            self.interval_field,
                            ft.ElevatedButton(
                                "💾 Save",
                                on_click=on_save_settings,
                                bgcolor=Theme.ACCENT_BLUE + "22",
                                color=Theme.ACCENT_BLUE,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            ),
                        ]),
                    ]),
                    padding=8,
                    bgcolor=Theme.BG_CARD,
                    border=ft.Border.all(1, Theme.BORDER),
                    border_radius=8,
                ),
                # Platform accounts
                ft.Container(
                    content=ft.Column([
                        ft.Text("Platform Accounts", weight=ft.FontWeight.W_600, size=14, color=Theme.TEXT_SECONDARY),
                        ft.Row([
                            self.add_platform_dropdown,
                            self.add_account_name,
                            self.add_account_api_key,
                            ft.ElevatedButton(
                                "➕ Add",
                                on_click=on_add_account,
                                bgcolor=Theme.ACCENT_GREEN + "22",
                                color=Theme.ACCENT_GREEN,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            ),
                        ], wrap=True, spacing=8),
                        self.accounts_list_view,
                    ]),
                    padding=8,
                    bgcolor=Theme.BG_CARD,
                    border=ft.Border.all(1, Theme.BORDER),
                    border_radius=8,
                    expand=True,
                ),
                # Actions
                ft.Container(
                    content=ft.Column([
                        ft.Text("Actions", weight=ft.FontWeight.W_600, size=14, color=Theme.TEXT_SECONDARY),
                        ft.Row([
                            ft.ElevatedButton(
                                "🗑 Clear History",
                                on_click=on_clear_history,
                                bgcolor=Theme.ACCENT_RED + "22",
                                color=Theme.ACCENT_RED,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            ),
                            ft.ElevatedButton(
                                "📦 Export Data",
                                on_click=on_export_data,
                                bgcolor=Theme.ACCENT_AMBER + "22",
                                color=Theme.ACCENT_AMBER,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                            ),
                        ]),
                    ]),
                    padding=8,
                    bgcolor=Theme.BG_CARD,
                    border=ft.Border.all(1, Theme.BORDER),
                    border_radius=8,
                ),
                # About
                ft.Container(
                    content=ft.Column([
                        ft.Text("About", weight=ft.FontWeight.W_600, size=14, color=Theme.TEXT_SECONDARY),
                        ft.Text("Social Media Scheduler Pro v1.0.0", size=12, color=Theme.TEXT_PRIMARY),
                        ft.Text("Built with Flet • Cross-platform desktop app", size=11, color=Theme.TEXT_MUTED),
                        ft.Text("Supports: Twitter/X, Telegram, Reddit, Discord, Instagram, LinkedIn, TikTok", size=10, color=Theme.TEXT_MUTED),
                    ]),
                    padding=8,
                    bgcolor=Theme.BG_CARD,
                    border=ft.Border.all(1, Theme.BORDER),
                    border_radius=8,
                ),
                settings_status,
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            expand=True,
        )

    # ===== Event Handlers =====

    def _on_post_click(self, post: ScheduledPost):
        """Handle post card click — show details."""
        content_preview = ft.Text(post.content, size=12, color=Theme.TEXT_PRIMARY, selectable=True)
        items = [
            ft.Row([
                build_platform_badge(post.platform),
                ft.Container(
                    content=ft.Text(post.status.value.upper(), size=10, weight=ft.FontWeight.W_600,
                                    color=get_status_color(post.status)),
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    bgcolor=get_status_color(post.status) + "22",
                    border_radius=4,
                ),
            ]),
            ft.Divider(color=Theme.BORDER, height=1),
            content_preview,
        ]

        if post.thread_posts:
            items.append(ft.Text(f"🧵 Thread: {len(post.thread_posts)} additional posts", size=11, color=Theme.TEXT_SECONDARY))
        if post.scheduled_at:
            items.append(ft.Text(f"📅 Scheduled: {post.scheduled_at.replace('T', ' ')}", size=11, color=Theme.TEXT_SECONDARY))
        if post.posted_at:
            items.append(ft.Text(f"✅ Posted: {post.posted_at.replace('T', ' ')}", size=11, color=Theme.TEXT_SECONDARY))
            items.append(ft.Text(f"❤️ {post.engagement.get('likes', 0)} Likes", size=11, color=Theme.TEXT_SECONDARY))
        if post.error_message:
            items.append(ft.Text(f"❌ Error: {post.error_message}", size=11, color=Theme.ACCENT_RED))
        if post.recurring:
            items.append(ft.Text(f"🔄 Recurring: {post.recurring}", size=11, color=Theme.ACCENT_AMBER))

        dialog = ft.AlertDialog(
            title=ft.Text(f"Post #{post.id} — {post.platform.value.capitalize()}", weight=ft.FontWeight.BOLD, color=Theme.TEXT_PRIMARY),
            content=ft.Container(
                content=ft.Column(items, spacing=6, scroll=ft.ScrollMode.AUTO),
                width=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.page.close(dialog)),
            ],
        )
        self.page.open(dialog)
        self.page.update()

    def _on_delete_post(self, post: ScheduledPost):
        """Handle post deletion."""
        self.scheduler.cancel_post(post.id)
        self._refresh_all()
        self._update_status(f"🗑 Deleted post #{post.id}")

    def _on_post_start(self, post: ScheduledPost):
        """Callback when a post starts posting."""
        self._update_status(f"🔄 Posting to {post.platform.value}...", Theme.ACCENT_AMBER)
        self._refresh_queue()

    def _on_post_success(self, post: ScheduledPost):
        """Callback when a post succeeds."""
        self._update_status(f"✅ Posted to {post.platform.value}!", Theme.ACCENT_GREEN)
        self._refresh_all()

    def _on_post_fail(self, post: ScheduledPost):
        """Callback when a post fails."""
        self._update_status(f"❌ Failed to post to {post.platform.value}", Theme.ACCENT_RED)
        self._refresh_all()

    # ===== Helpers =====

    def _refresh_all(self):
        """Refresh all views."""
        self._refresh_upcoming()
        self._refresh_queue()
        self._refresh_analytics()
        self._refresh_accounts()

    def _refresh_accounts(self):
        """Refresh accounts list in settings."""
        self.accounts_list_view.controls.clear()
        accounts = get_accounts()
        for acct in accounts:
            color = get_platform_color(acct.platform)
            emoji = get_platform_emoji(acct.platform)
            self.accounts_list_view.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{emoji} {acct.name}", size=12, color=color),
                        ft.Text(f"({acct.platform.value})", size=10, color=Theme.TEXT_MUTED),
                        ft.Container(expand=True),
                        ft.Text("🟢 Active" if acct.is_active else "🔴 Inactive", size=10, color=Theme.ACCENT_GREEN if acct.is_active else Theme.ACCENT_RED),
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE,
                            icon_size=14,
                            icon_color=Theme.TEXT_MUTED,
                            on_click=lambda _, aid=acct.id: self._on_delete_account(aid),
                        ),
                    ]),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=Theme.BG_INPUT,
                    border_radius=4,
                )
            )
        if not accounts:
            self.accounts_list_view.controls.append(
                ft.Text("No accounts added yet", size=11, color=Theme.TEXT_MUTED)
            )
        self.accounts_list_view.update()

    def _on_delete_account(self, account_id: int):
        """Delete a platform account."""
        delete_account(account_id)
        self._refresh_accounts()
        self._refresh_analytics()

    def _update_scheduler_status(self):
        """Update the scheduler status indicator."""
        if self.scheduler._running:
            self.scheduler_status.value = "● Running"
            self.scheduler_status.color = Theme.ACCENT_GREEN
        else:
            self.scheduler_status.value = "● Stopped"
            self.scheduler_status.color = Theme.ACCENT_RED
        try:
            self.scheduler_status.update()
        except Exception:
            pass

    def _update_status(self, text: str, color: str = Theme.TEXT_SECONDARY):
        """Update the status bar text."""
        try:
            self.status_text.value = text
            self.status_text.color = color
            self.status_text.update()
        except Exception:
            pass

    def shutdown(self):
        """Clean shutdown."""
        if hasattr(self, 'scheduler'):
            self.scheduler.stop()
