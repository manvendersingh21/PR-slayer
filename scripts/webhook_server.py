#!/usr/bin/env python3
"""
Lightweight Webhook Server & GitHub PR Monitor Bridge.
- Listens for GitHub Actions or external webhook payloads and dispatches iMessages on macOS.
- Provides REST endpoints for live GitHub PR status and daemon controls.
Zero external dependencies (uses standard library http.server).
"""

import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Add scripts directory to path to import notifier and watcher
sys.path.insert(0, str(Path(__file__).parent))
from pr_imessage_notifier import generate_message, send_imessage, load_dotenv
from github_pr_watcher import (
    get_github_user, fetch_user_prs, evaluate_pr_status,
    check_and_notify, daemon_status, daemon_start, daemon_stop
)

load_dotenv()

PORT = int(os.getenv("PORT", 8080))
DEFAULT_RECIPIENT = os.getenv("IMESSAGE_RECIPIENT", "")

class WebhookHandler(BaseHTTPRequestHandler):
    def _send_response(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self._send_response(200, {"status": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        recipient = params.get("recipient", [DEFAULT_RECIPIENT])[0]

        if parsed.path == "/health":
            self._send_response(200, {
                "status": "healthy",
                "recipient_configured": bool(DEFAULT_RECIPIENT),
                "github_user": get_github_user()
            })
            return

        if parsed.path == "/github/status":
            self._send_response(200, {
                "github_user": get_github_user(),
                "daemon_running": daemon_status(),
                "recipient": recipient or "(not configured)"
            })
            return

        if parsed.path == "/github/prs":
            user = get_github_user()
            raw_prs = fetch_user_prs()
            detailed = []
            for pr in raw_prs:
                repo = pr.get("repository", {}).get("nameWithOwner", "")
                num = pr.get("number")
                title = pr.get("title", "")
                url = pr.get("url", "")
                status, reasons, _ = evaluate_pr_status(url)
                detailed.append({
                    "repo": repo,
                    "number": num,
                    "title": title,
                    "url": url,
                    "status": status,
                    "reasons": reasons
                })
            self._send_response(200, {"user": user, "prs": detailed})
            return

        if parsed.path == "/test/fail":
            msg = generate_message(
                status="fail",
                pr_number=params.get("pr", ["404"])[0],
                pr_title=params.get("title", ["Emergency hotfix gone wrong"])[0],
                author=params.get("author", [get_github_user()])[0],
                env="production"
            )
            sent = False
            if recipient:
                sent = send_imessage(recipient, msg)
            self._send_response(200, {
                "outcome": "fail",
                "recipient": recipient or "(not set)",
                "sent": sent,
                "message": msg
            })
            return

        if parsed.path == "/test/pass":
            msg = generate_message(
                status="pass",
                pr_number=params.get("pr", ["200"])[0],
                pr_title=params.get("title", ["Refactor database index"])[0],
                author=params.get("author", [get_github_user()])[0],
                env="production"
            )
            sent = False
            if recipient:
                sent = send_imessage(recipient, msg)
            self._send_response(200, {
                "outcome": "pass",
                "recipient": recipient or "(not set)",
                "sent": sent,
                "message": msg
            })
            return

        self._send_response(404, {"error": "Endpoint not found."})

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            payload = json.loads(body) if body else {}
        except Exception as e:
            self._send_response(400, {"error": f"Invalid JSON body: {str(e)}"})
            return

        recipient = payload.get("recipient") or DEFAULT_RECIPIENT

        if parsed.path == "/github/check":
            dry_run = payload.get("dry_run", False)
            changes = check_and_notify(recipient=recipient, dry_run=dry_run, verbose=False)
            self._send_response(200, {
                "status": "success",
                "changes_detected": changes,
                "recipient": recipient or "(none)"
            })
            return

        if parsed.path == "/github/daemon/start":
            interval = payload.get("interval", 60)
            daemon_start(interval=interval, recipient=recipient)
            self._send_response(200, {"status": "daemon_started", "running": True})
            return

        if parsed.path == "/github/daemon/stop":
            daemon_stop()
            self._send_response(200, {"status": "daemon_stopped", "running": False})
            return

        if parsed.path in ("/webhook", "/notify"):
            status = payload.get("status") or payload.get("conclusion") or payload.get("action")
            env = payload.get("environment") or payload.get("env") or "production"
            repo = payload.get("repository", {}).get("full_name") or payload.get("repo")
            pr_number = payload.get("pr_number") or payload.get("number")
            pr_title = payload.get("pr_title") or payload.get("title")
            author = payload.get("author") or payload.get("sender", {}).get("login")
            dry_run = payload.get("dry_run", False)

            if not status:
                self._send_response(400, {"error": "Missing 'status' in JSON payload ('fail' or 'pass')"})
                return

            message = generate_message(
                status=status,
                pr_number=pr_number,
                pr_title=pr_title,
                author=author,
                repo=repo,
                env=env
            )

            result = {
                "environment": env,
                "status": status,
                "recipient": recipient or "(none)",
                "message": message,
                "dry_run": dry_run,
                "delivered": False
            }

            if dry_run or not recipient:
                result["note"] = "No message sent (dry run or missing recipient)"
                self._send_response(200, result)
                return

            delivered = send_imessage(recipient, message)
            result["delivered"] = delivered
            status_code = 200 if delivered else 500
            self._send_response(status_code, result)
            return

        self._send_response(404, {"error": "Not found. POST to /webhook, /notify, or /github/check"})

def run():
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    user = get_github_user()
    print(f"🚀 PR iMessage Webhook Server listening on http://0.0.0.0:{PORT}")
    print(f"🐙 Connected GitHub Account: @{user}")
    print(f"📱 Default Recipient: {DEFAULT_RECIPIENT or '(Set IMESSAGE_RECIPIENT in .env)'}")
    print("\nEndpoints:")
    print(f"  • GET  /github/prs    - List your tracked PRs with live CI status")
    print(f"  • POST /github/check  - Trigger a manual check and notification")
    print(f"  • POST /webhook       - Receive GitHub Actions webhook events")
    print(f"  • GET  /test/fail     - Test Shakespeare insult")
    print(f"  • GET  /test/pass     - Test Cold Guy ('you couldve done better') nod")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

if __name__ == "__main__":
    run()
