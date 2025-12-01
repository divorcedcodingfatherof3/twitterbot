"""Vercel serverless entrypoint to run the dice-reply bot."""
import json
from http.server import BaseHTTPRequestHandler

from lib.bot import env_runtime_params, run_bot_once


class handler(BaseHTTPRequestHandler):
    """
    Execute the bot via a Vercel serverless function.

    Environment variables:
    - TARGET_USERNAME: profile to monitor (default sponsetavnav)
    - TWEET_LIMIT: number of tweets to scan (default 5)
    - STATE_FILE: optional path for replied IDs (default /tmp/replied.json)
    - DRY_RUN: if truthy, only log intended replies
    - REPLY_BACKLOG: if truthy, reply to the current backlog when no state exists
    """

    def do_GET(self):
        username, limit, state_file, dry_run, reply_backlog = env_runtime_params()

        try:
            run_bot_once(
                username=username,
                limit=limit,
                state_file=state_file,
                dry_run=dry_run,
                reply_backlog=reply_backlog,
            )
            status_code = 200
            body = {
                "ok": True,
                "username": username,
                "limit": limit,
                "dry_run": dry_run,
                "reply_backlog": reply_backlog,
            }
        except Exception as exc:  # pragma: no cover - surfaced in Vercel response
            status_code = 500
            body = {
                "ok": False,
                "error": str(exc),
                "username": username,
                "limit": limit,
                "dry_run": dry_run,
                "reply_backlog": reply_backlog,
            }

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))
