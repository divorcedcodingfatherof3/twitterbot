"""HTTP endpoint to trigger a single bot run."""
import json
from http.server import BaseHTTPRequestHandler

from lib.bot import env_runtime_params, run_bot_once


class handler(BaseHTTPRequestHandler):  # Vercel forventer en klasse med dette navnet
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
            body = {"ok": True}
        except Exception as exc:  # pragma: no cover - returneres i HTTP-respons
            print(f"Failed to run bot: {exc}")
            status_code = 500
            body = {"ok": False, "error": str(exc)}

        # Svar til klienten (Vercel bruker dette som HTTP-respons)
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))
