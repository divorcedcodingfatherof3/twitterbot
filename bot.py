"""
Twitter bot to reply to @sponsetavnav tweets with a Norwegian dice rating.
"""
import argparse
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Set

import tweepy
from dotenv import load_dotenv


DEFAULT_USERNAME = "sponsetavnav"
STATE_PATH = Path("data/replied.json")


@dataclass
class BotState:
    """Persistent state tracking replied tweet IDs and newest seen tweet."""

    replied_ids: Set[str]
    since_id: Optional[str] = None


class BotConfig:
    """Configuration for the bot loaded from environment variables."""

    def __init__(self) -> None:
        load_dotenv()
        try:
            self.api_key = os.environ["X_API_KEY"]
            self.api_secret = os.environ["X_API_SECRET"]
            self.access_token = os.environ["X_ACCESS_TOKEN"]
            self.access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"]
        except KeyError as exc:
            missing = exc.args[0]
            raise RuntimeError(
                f"Missing required environment variable '{missing}'. "
                "Check your .env file or shell environment."
            ) from exc

    def client(self) -> tweepy.Client:
        return tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True,
        )


def load_state(path: Path) -> BotState:
    if not path.exists():
        return BotState(replied_ids=set(), since_id=None)

    with path.open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError:
            return BotState(replied_ids=set(), since_id=None)

    # Backward compatibility: plain list of IDs
    if isinstance(data, list):
        return BotState({str(item) for item in data if isinstance(item, (int, str))}, None)

    if not isinstance(data, dict):
        return BotState(replied_ids=set(), since_id=None)

    replied_ids: Set[str] = set()
    raw_ids = data.get("replied_ids")
    if isinstance(raw_ids, list):
        replied_ids = {str(item) for item in raw_ids if isinstance(item, (int, str))}

    since_id = data.get("since_id")
    since_id_str: Optional[str] = None
    if isinstance(since_id, (int, str)):
        since_id_str = str(since_id)

    return BotState(replied_ids=replied_ids, since_id=since_id_str)


def save_state(path: Path, state: BotState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "replied_ids": sorted(state.replied_ids),
        "since_id": state.since_id,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def pick_dice_score() -> int:
    return random.randint(1, 6)


def build_reply_text(score: int) -> str:
    return f"Jeg gir denne posten terningkast {score} 🎲"


def fetch_recent_tweets(
    client: tweepy.Client, user_id: str, limit: int, since_id: Optional[str]
) -> list[tweepy.Tweet]:
    response = client.get_users_tweets(
        id=user_id,
        max_results=min(limit, 100),
        exclude=["retweets", "replies"],
        tweet_fields=["id", "text", "created_at"],
        since_id=since_id,
    )
    return response.data or []


def resolve_user_id(client: tweepy.Client, username: str) -> str:
    result = client.get_user(username=username)
    if result.data is None:
        raise RuntimeError(f"Could not resolve user '{username}'")
    return str(result.data.id)


def reply_to_new_tweets(
    client: tweepy.Client,
    tweets: Iterable[tweepy.Tweet],
    replied_ids: Set[str],
    dry_run: bool,
) -> Set[str]:
    updated_ids = set(replied_ids)
    for tweet in tweets:
        tweet_id = str(tweet.id)
        if tweet_id in updated_ids:
            continue

        score = pick_dice_score()
        message = build_reply_text(score)

        if dry_run:
            print(f"[DRY RUN] Would reply to {tweet_id}: {message}")
        else:
            client.create_tweet(text=message, in_reply_to_tweet_id=tweet_id)
            print(f"Replied to tweet {tweet_id} with score {score}")

        updated_ids.add(tweet_id)
    return updated_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reply to tweets with a dice score in Norwegian.")
    state_override = os.getenv("STATE_FILE")
    state_default = Path(state_override) if state_override else STATE_PATH

    parser.add_argument(
        "--username",
        default=os.getenv("TARGET_USERNAME", DEFAULT_USERNAME),
        help="Target username to monitor (without @).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
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


def run_bot(
    username: str,
    limit: int,
    state_file: Path,
    dry_run: bool,
    reply_backlog: bool = False,
) -> None:
    config = BotConfig()
    client = config.client()

    print(
        f"Monitoring @{username} for new tweets; "
        f"limit={limit}; dry_run={dry_run}; state_file={state_file}; "
        f"reply_backlog={reply_backlog}"
    )

    user_id = resolve_user_id(client, username)
    state = load_state(state_file)

    since_id = state.since_id or (max(state.replied_ids) if state.replied_ids else None)

    # Avoid replying to old tweets on first run unless explicitly requested
    if since_id is None and not reply_backlog:
        baseline = fetch_recent_tweets(client, user_id, limit=1, since_id=None)
        if baseline:
            since_id = str(baseline[0].id)
            state.since_id = since_id
            print(
                "No existing state; bootstrapping from the latest tweet to avoid "
                "replying to older posts."
            )

    tweets = fetch_recent_tweets(client, user_id, limit, since_id)

    updated_ids = reply_to_new_tweets(client, tweets, state.replied_ids, dry_run)
    if tweets:
        state.since_id = max([str(tweet.id) for tweet in tweets] + ([state.since_id] if state.since_id else []))
    state.replied_ids = updated_ids
    save_state(state_file, state)


def main() -> None:
    args = parse_args()
    run_bot(
        username=args.username,
        limit=args.limit,
        state_file=args.state_file,
        dry_run=args.dry_run,
        reply_backlog=args.reply_backlog,
    )


if __name__ == "__main__":
    main()
