"""
Optional Xquik helpers for adding live X source context to scheduled threads.
"""
import json
import os
from typing import Dict, List
from urllib import parse, request
from urllib.error import HTTPError, URLError


XQUIK_API_BASE = "https://xquik.com/api/v1"


def fetch_xquik_tweet_examples(query: str, limit: int = 2) -> List[Dict[str, str]]:
    """Fetch tweet examples from Xquik for an optional schedule topic."""
    api_key = os.environ.get("XQUIK_API_KEY", "").strip()
    if not api_key or not query.strip():
        return []

    base_url = os.environ.get("XQUIK_API_BASE_URL", XQUIK_API_BASE).rstrip("/")
    params = parse.urlencode({
        "q": query.strip(),
        "limit": max(1, min(limit, 5)),
        "queryType": "Top",
    })
    url = f"{base_url}/x/tweets/search?{params}"
    req = request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "social-media-scheduler-pro/1.0",
        },
        method="GET",
    )

    try:
        with request.urlopen(req, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        return []

    tweets = payload.get("tweets")
    if not isinstance(tweets, list):
        return []

    examples = []
    for tweet in tweets:
        if not isinstance(tweet, dict):
            continue
        text = str(tweet.get("text") or "").strip()
        if not text:
            continue
        author = tweet.get("author") if isinstance(tweet.get("author"), dict) else {}
        username = str(author.get("username") or "").strip()
        tweet_id = str(tweet.get("id") or "").strip()
        examples.append({
            "text": " ".join(text.split())[:180],
            "username": username,
            "url": f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else "",
        })
        if len(examples) >= limit:
            break
    return examples


def build_xquik_source_notes(query: str, limit: int = 2) -> List[str]:
    """Convert Xquik tweet examples into short thread source notes."""
    notes = []
    for example in fetch_xquik_tweet_examples(query, limit=limit):
        byline = f"@{example['username']}: " if example.get("username") else ""
        url = f" {example['url']}" if example.get("url") else ""
        notes.append(f"Source via Xquik: {byline}{example['text']}{url}")
    return notes
