"""Vercel serverless entrypoint to run the dice-reply bot."""
import json

from lib.bot import env_runtime_params, run_bot_once


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
    username, limit, state_file, dry_run, reply_backlog = env_runtime_params()

    try:
        run_bot_once(
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
