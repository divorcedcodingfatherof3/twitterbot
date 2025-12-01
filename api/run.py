"""Vercel serverless entrypoint to run the dice-reply bot."""
import json
import os
from pathlib import Path

from bot import DEFAULT_USERNAME, run_bot


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def handler(request):  # type: ignore[unused-argument]
    """
    Execute the bot via a Vercel serverless function.

    Environment variables:
    - TARGET_USERNAME: profile to monitor (default sponsetavnav)
    - TWEET_LIMIT: number of tweets to scan (default 5)
    - STATE_FILE: optional path for replied IDs (default /tmp/replied.json)
    - DRY_RUN: if truthy, only log intended replies
    - REPLY_BACKLOG: if truthy, reply to the current backlog when no state exists
    """
    username = os.getenv("TARGET_USERNAME", DEFAULT_USERNAME)
    limit = int(os.getenv("TWEET_LIMIT", "5"))
    state_file = Path(os.getenv("STATE_FILE", "/tmp/replied.json"))
    dry_run = _env_bool("DRY_RUN", False)
    reply_backlog = _env_bool("REPLY_BACKLOG", False)

    try:
        run_bot(
            username=username,
            limit=limit,
            state_file=state_file,
            dry_run=dry_run,
            reply_backlog=reply_backlog,
        )
    except Exception as exc:  # pragma: no cover - surfaced in Vercel response
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "ok": False,
                "error": str(exc),
                "username": username,
                "limit": limit,
                "dry_run": dry_run,
                "reply_backlog": reply_backlog,
            }),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "ok": True,
            "username": username,
            "limit": limit,
            "dry_run": dry_run,
            "reply_backlog": reply_backlog,
        }),
    }
