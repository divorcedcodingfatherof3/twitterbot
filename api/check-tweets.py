"""HTTP endpoint to trigger a single bot run."""
import json

from lib.bot import env_runtime_params, run_bot_once


def handler(request):  # type: ignore[unused-argument]
    username, limit, state_file, dry_run, reply_backlog = env_runtime_params()

    try:
        run_bot_once(
            username=username,
            limit=limit,
            state_file=state_file,
            dry_run=dry_run,
            reply_backlog=reply_backlog,
        )
    except Exception as exc:  # pragma: no cover - returned in HTTP response
        print(f"Failed to run bot: {exc}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False}),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"ok": True}),
    }
