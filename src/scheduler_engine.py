"""
Scheduler engine — uses APScheduler to dispatch posts at scheduled times.
"""
import logging
import threading
import time
from datetime import datetime
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .models import ScheduledPost, PostStatus, Platform
from .database import (
    get_posts, update_post_status, save_post, record_post_history,
    update_post_engagement,
)
from .platforms.factory import get_platform_handler, get_all_platforms

logger = logging.getLogger(__name__)


class SchedulerEngine:
    """Background scheduler that checks for due posts and dispatches them."""

    def __init__(self, interval: int = 30):
        self.interval = interval
        self.scheduler = BackgroundScheduler()
        self._running = False
        self._lock = threading.Lock()
        self._queue: List[ScheduledPost] = []
        self._callbacks = {
            "on_post_start": [],
            "on_post_success": [],
            "on_post_fail": [],
        }

    def on(self, event: str, callback):
        """Register event callback."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _notify(self, event: str, post: ScheduledPost):
        """Notify all listeners of an event."""
        for cb in self._callbacks.get(event, []):
            try:
                cb(post)
            except Exception as e:
                logger.error(f"[Scheduler] Callback error: {e}")

    def start(self):
        """Start the background scheduler."""
        if self._running:
            return
        self._running = True

        # Add the check job
        self.scheduler.add_job(
            self._check_pending_posts,
            IntervalTrigger(seconds=self.interval),
            id="check_pending",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info(f"[Scheduler] Started with {self.interval}s check interval")

    def stop(self):
        """Stop the background scheduler."""
        self._running = False
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped")

    def schedule_post(self, post: ScheduledPost) -> bool:
        """Add a post to the schedule."""
        if post.status == PostStatus.DRAFT:
            post.status = PostStatus.SCHEDULED
        save_post(post)
        with self._lock:
            self._queue.append(post)
        logger.info(f"[Scheduler] Scheduled post #{post.id} for {post.platform.value}")
        return True

    def cancel_post(self, post_id: int) -> bool:
        """Cancel a scheduled post."""
        from .database import delete_post
        delete_post(post_id)
        with self._lock:
            self._queue = [p for p in self._queue if p.id != post_id]
        logger.info(f"[Scheduler] Cancelled post #{post_id}")
        return True

    def get_queue(self) -> List[ScheduledPost]:
        """Get the current post queue."""
        with self._lock:
            return list(self._queue)

    def _check_pending_posts(self):
        """Check for posts that need to be dispatched (called periodically)."""
        try:
            now = datetime.now().isoformat()
            pending = get_posts(status_filter=PostStatus.SCHEDULED.value)

            for post in pending:
                # Skip posts without a schedule time
                if not post.scheduled_at:
                    continue

                # Check if it's time to post
                if post.scheduled_at <= now:
                    self._dispatch_post(post)

        except Exception as e:
            logger.error(f"[Scheduler] Check error: {e}")

    def _dispatch_post(self, post: ScheduledPost):
        """Dispatch a single post to its platform."""
        logger.info(f"[Scheduler] Dispatching post #{post.id} to {post.platform.value}")

        # Mark as posting
        post.status = PostStatus.POSTING
        save_post(post)
        self._notify("on_post_start", post)

        try:
            # Get the platform handler
            handler = get_platform_handler(post.platform)

            # Post with optional media
            success = handler.post(post.content, post.media_path)

            # Handle thread posts
            if success and post.thread_posts:
                for thread_post in post.thread_posts:
                    handler.post(thread_post)

            if success:
                post.status = PostStatus.POSTED
                post.posted_at = datetime.now().isoformat()

                # Get engagement metrics
                try:
                    post.engagement = handler.get_engagement(str(post.id))
                except Exception:
                    post.engagement = {"likes": 0, "retweets": 0, "replies": 0, "impressions": 0}

                save_post(post)
                record_post_history(post, success=True)
                update_post_engagement(post.id, post.engagement)

                self._notify("on_post_success", post)
                logger.info(f"[Scheduler] Post #{post.id} to {post.platform.value} succeeded")
            else:
                raise Exception("Platform handler returned False")

        except Exception as e:
            error_msg = str(e)[:200]
            logger.error(f"[Scheduler] Post #{post.id} to {post.platform.value} failed: {error_msg}")

            post.status = PostStatus.FAILED
            post.error_message = error_msg
            save_post(post)
            record_post_history(post, success=False)
            self._notify("on_post_fail", post)
