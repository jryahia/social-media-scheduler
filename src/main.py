#!/usr/bin/env python3
"""
Social Media Scheduler Pro — Desktop App Entry Point.
Cross-platform desktop app for scheduling posts across 7 social platforms.

Usage:
    python3 src/main.py
"""
import sys
import os

# Ensure we're in the right directory
APP_DIR = os.path.expanduser("~/.hermes/profiles/codex/workspace/projects/social_scheduler")
if os.path.exists(APP_DIR):
    sys.path.insert(0, APP_DIR)

import flet as ft

from src.ui.app import SocialSchedulerApp


def main():
    """Run the Social Media Scheduler Pro desktop app."""
    ft.app(
        target=_run_app,
        name="SocialSchedulerPro",
        assets_dir=None,
    )


def _run_app(page: ft.Page):
    """Initialize and run the app on a page."""
    app = SocialSchedulerApp(page)
    page.on_close = app.shutdown


if __name__ == "__main__":
    # Create data directory
    os.makedirs(os.path.join(APP_DIR, "data"), exist_ok=True)

    # Install dependencies if needed
    try:
        import flet
        import apscheduler
    except ImportError:
        print("Installing dependencies...")
        import subprocess
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r",
             os.path.join(APP_DIR, "requirements.txt")]
        )

    main()
