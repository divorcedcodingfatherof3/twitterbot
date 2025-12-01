"""
Twitter bot to reply to @sponsetavnav tweets with a Norwegian dice rating.
"""
import argparse
from pathlib import Path

from lib.bot import env_runtime_params, run_bot_once


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reply to tweets with a dice score in Norwegian.")
    username_default, limit_default, state_default, _, _ = env_runtime_params()

    parser.add_argument(
        "--username",
        default=username_default,
        help="Target username to monitor (without @).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=limit_default,
        help="Number of recent tweets to check for replies.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=state_default,
        help="Path to store the list of tweet IDs already replied to.",
    )
    parser.add_argument(
        "--reply-backlog",
        action="store_true",
        help=(
            "If set, reply to currently available tweets when no state exists. "
            "By default the bot bootstraps from the latest tweet to avoid spamming old posts."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without posting replies to Twitter.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_bot_once(
        username=args.username,
        limit=args.limit,
        state_file=args.state_file,
        dry_run=args.dry_run,
        reply_backlog=args.reply_backlog,
    )


if __name__ == "__main__":
    main()
