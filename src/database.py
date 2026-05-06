"""
SQLite database for Social Media Scheduler Pro.
"""
import json
import sqlite3
import os
from datetime import datetime
from typing import List, Optional

from .models import ScheduledPost, PostStatus, Platform, PlatformAccount
from .utils import DATA_DIR, DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            media_path TEXT,
            scheduled_at TEXT,
            status TEXT DEFAULT 'draft',
            created_at TEXT NOT NULL,
            posted_at TEXT,
            thread_posts TEXT,
            recurring TEXT,
            engagement TEXT DEFAULT '{}',
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_posts_status ON scheduled_posts(status);
        CREATE INDEX IF NOT EXISTS idx_posts_platform ON scheduled_posts(platform);
        CREATE INDEX IF NOT EXISTS idx_posts_scheduled ON scheduled_posts(scheduled_at);

        CREATE TABLE IF NOT EXISTS platform_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            name TEXT NOT NULL,
            credentials TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            added_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_accounts_platform ON platform_accounts(platform);

        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            media_path TEXT,
            thread_posts TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS post_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            platform TEXT NOT NULL,
            content TEXT,
            posted_at TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            success INTEGER DEFAULT 1,
            error_message TEXT
        );
    """)

    conn.commit()
    conn.close()


# --- Scheduled Posts ---

def save_post(post: ScheduledPost) -> int:
    """Save a scheduled post. Returns the post ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        now = datetime.now().isoformat()
        if post.id == 0:
            cursor.execute(
                """INSERT INTO scheduled_posts
                   (platform, content, media_path, scheduled_at, status, created_at,
                    thread_posts, recurring, engagement)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    post.platform.value, post.content, post.media_path,
                    post.scheduled_at, post.status.value, now,
                    ",".join(post.thread_posts), post.recurring,
                    json.dumps(post.engagement),
                ),
            )
            post.id = cursor.lastrowid
            post.created_at = now
        else:
            cursor.execute(
                """UPDATE scheduled_posts SET
                   platform=?, content=?, media_path=?, scheduled_at=?, status=?,
                   thread_posts=?, recurring=?, engagement=?, error_message=?, posted_at=?
                   WHERE id=?""",
                (
                    post.platform.value, post.content, post.media_path,
                    post.scheduled_at, post.status.value,
                    ",".join(post.thread_posts), post.recurring,
                    json.dumps(post.engagement), post.error_message,
                    post.posted_at, post.id,
                ),
            )
        conn.commit()
        return post.id
    finally:
        conn.close()


def get_posts(status_filter: Optional[str] = None, platform_filter: Optional[str] = None) -> List[ScheduledPost]:
    """Get scheduled posts with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM scheduled_posts WHERE 1=1"
        params = []
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        if platform_filter:
            query += " AND platform = ?"
            params.append(platform_filter)
        query += " ORDER BY scheduled_at ASC"
        cursor.execute(query, params)
        return [_row_to_post(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_upcoming_posts(limit: int = 20) -> List[ScheduledPost]:
    """Get upcoming scheduled posts."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT * FROM scheduled_posts
               WHERE status IN ('scheduled', 'posting')
               ORDER BY scheduled_at ASC LIMIT ?""",
            (limit,),
        )
        return [_row_to_post(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_post_status(post_id: int, status: PostStatus, error_message: Optional[str] = None):
    """Update a post's status."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        now = datetime.now().isoformat()
        posted_at = now if status == PostStatus.POSTED else None
        cursor.execute(
            """UPDATE scheduled_posts SET status=?, posted_at=?, error_message=?
               WHERE id=?""",
            (status.value, posted_at, error_message, post_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_post(post_id: int):
    """Delete a scheduled post."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM scheduled_posts WHERE id = ?", (post_id,))
        conn.commit()
    finally:
        conn.close()


def record_post_history(post: ScheduledPost, success: bool = True):
    """Record a posted post in history for analytics."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO post_history
               (post_id, platform, content, posted_at, success, error_message)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                post.id, post.platform.value, post.content[:200],
                post.posted_at or datetime.now().isoformat(),
                int(success), post.error_message,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def update_post_engagement(post_id: int, engagement: dict):
    """Update engagement stats for a post."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE scheduled_posts SET engagement = ? WHERE id = ?""",
            (json.dumps(engagement), post_id),
        )
        conn.commit()
        # Also update post_history
        cursor.execute(
            """UPDATE post_history SET likes=?, retweets=?, replies=?, impressions=?
               WHERE post_id=?""",
            (
                engagement.get("likes", 0),
                engagement.get("retweets", 0),
                engagement.get("replies", 0),
                engagement.get("impressions", 0),
                post_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


# --- Drafts ---

def save_draft(platform: str, content: str, media_path: Optional[str] = None,
               thread_posts: Optional[List[str]] = None) -> int:
    """Save a draft. Returns the draft ID."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute(
            """INSERT INTO drafts (platform, content, media_path, thread_posts, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (platform, content, media_path, ",".join(thread_posts or []), now, now),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_drafts() -> List[dict]:
    """Get all drafts."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM drafts ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# --- Platform Accounts ---

def save_account(account: PlatformAccount) -> int:
    """Save a platform account. Returns the account ID."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        if account.id == 0:
            cursor.execute(
                """INSERT INTO platform_accounts (platform, name, credentials, is_active, added_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (account.platform.value, account.name, json.dumps(account.credentials),
                 int(account.is_active), now),
            )
            account.id = cursor.lastrowid
        else:
            cursor.execute(
                """UPDATE platform_accounts SET platform=?, name=?, credentials=?,
                   is_active=? WHERE id=?""",
                (account.platform.value, account.name, json.dumps(account.credentials),
                 int(account.is_active), account.id),
            )
        conn.commit()
        return account.id
    finally:
        conn.close()


def get_accounts() -> List[PlatformAccount]:
    """Get all platform accounts."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM platform_accounts ORDER BY added_at DESC")
        accounts = []
        for row in cursor.fetchall():
            acct = PlatformAccount(
                id=row["id"],
                platform=Platform(row["platform"]),
                name=row["name"],
                credentials=json.loads(row["credentials"]) if row["credentials"] else {},
                is_active=bool(row["is_active"]),
                added_at=row["added_at"],
            )
            accounts.append(acct)
        return accounts
    finally:
        conn.close()


def delete_account(account_id: int):
    """Delete a platform account."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM platform_accounts WHERE id = ?", (account_id,))
        conn.commit()
    finally:
        conn.close()


# --- Analytics ---

def get_analytics_summary() -> dict:
    """Get analytics summary data."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        result = {}
        # Total posts
        cursor.execute("SELECT COUNT(*) FROM scheduled_posts")
        result["total_posts"] = cursor.fetchone()[0]

        # Posted today
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM post_history WHERE posted_at LIKE ?",
            (f"{today}%",),
        )
        result["posted_today"] = cursor.fetchone()[0]

        # Success rate
        cursor.execute(
            "SELECT COUNT(*), SUM(success) FROM post_history",
        )
        row = cursor.fetchone()
        total = row[0] or 1
        success = row[1] or 0
        result["success_rate"] = round((success / total) * 100)

        # Active platforms
        cursor.execute(
            "SELECT COUNT(DISTINCT platform) FROM platform_accounts WHERE is_active = 1",
        )
        result["active_platforms"] = cursor.fetchone()[0]

        # Posts per platform
        cursor.execute(
            "SELECT platform, COUNT(*) as cnt FROM scheduled_posts GROUP BY platform ORDER BY cnt DESC",
        )
        result["per_platform"] = {row["platform"]: row["cnt"] for row in cursor.fetchall()}

        # Recent activity
        cursor.execute(
            "SELECT * FROM post_history ORDER BY posted_at DESC LIMIT 20",
        )
        result["recent_activity"] = [dict(row) for row in cursor.fetchall()]

        return result
    finally:
        conn.close()


def clear_post_history():
    """Clear all post history."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM post_history")
        cursor.execute("DELETE FROM scheduled_posts")
        conn.commit()
    finally:
        conn.close()


def _row_to_post(row) -> ScheduledPost:
    """Convert a DB row to a ScheduledPost object."""
    thread_posts = row["thread_posts"].split(",") if row["thread_posts"] else []
    engagement = {}
    try:
        engagement = json.loads(row["engagement"]) if row["engagement"] else {}
    except (json.JSONDecodeError, TypeError):
        pass
    return ScheduledPost(
        id=row["id"],
        platform=Platform(row["platform"]),
        content=row["content"],
        media_path=row["media_path"],
        scheduled_at=row["scheduled_at"],
        status=PostStatus(row["status"]),
        created_at=row["created_at"],
        posted_at=row["posted_at"],
        thread_posts=thread_posts,
        recurring=row["recurring"],
        engagement=engagement,
        error_message=row["error_message"],
    )
