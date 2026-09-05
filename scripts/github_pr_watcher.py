#!/usr/bin/env python3
"""
GitHub PR Watcher:
- Connects to your authenticated GitHub account via `gh` CLI.
- Automatically tracks your PRs across all repositories.
- Detects when CI checks complete, reviews change, or PRs merge/close.
- If your PR passes / is approved: Sends an iMessage from a cold person ("You could've done better on that PR").
- If your PR fails: Sends an iMessage mocking you like William Shakespeare.
- Keeps track of state in .pr_tracker_state.json to prevent duplicate notifications.
"""

import sys
import os
import json
import time
import argparse
import subprocess
import signal
from pathlib import Path
from datetime import datetime

# Import notifier engine
sys.path.insert(0, str(Path(__file__).parent))
from pr_imessage_notifier import generate_message, send_imessage, load_dotenv

load_dotenv()

STATE_FILE = Path(__file__).parent.parent / ".pr_tracker_state.json"
PID_FILE = Path(__file__).parent.parent / ".pr_watcher.pid"

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

def get_github_user():
    """Detect authenticated GitHub user via gh CLI."""
    out = run_cmd(["gh", "api", "user", "--jq", ".login"])
    if out:
        return out
    # Fallback to git config
    return run_cmd(["git", "config", "user.name"]) or "developer"

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def fetch_user_prs():
    """Find all open and recently updated PRs authored by @me."""
    out_open = run_cmd([
        "gh", "search", "prs", "--author", "@me", "--state", "open",
        "--json", "number,title,repository,url,updatedAt"
    ])
    out_closed = run_cmd([
        "gh", "search", "prs", "--author", "@me", "--state", "closed", "--limit", "5",
        "--json", "number,title,repository,url,updatedAt"
    ])

    prs = []
    seen = set()

    for out in (out_open, out_closed):
        if out:
            try:
                data = json.loads(out)
                for pr in data:
                    key = f"{pr.get('repository', {}).get('nameWithOwner', '')}#{pr.get('number')}"
                    if key not in seen:
                        seen.add(key)
                        prs.append(pr)
            except Exception:
                pass
    return prs

def evaluate_pr_status(pr_url):
    """
    Query GitHub for statusCheckRollup, reviewDecision, and state.
    Returns (status, reasons, details_dict)
    status: 'pass' | 'fail' | 'pending' | 'unknown'
    """
    out = run_cmd([
        "gh", "pr", "view", pr_url,
        "--json", "number,title,state,statusCheckRollup,reviewDecision,mergeable,commits"
    ])
    if not out:
        return "unknown", ["Failed to fetch PR details from GitHub"], {}

    try:
        data = json.loads(out)
    except Exception as e:
        return "unknown", [f"JSON parse error: {str(e)}"], {}

    state = data.get("state", "OPEN").upper()
    review = data.get("reviewDecision", "").upper()
    checks = data.get("statusCheckRollup", []) or []
    commits = data.get("commits", []) or []
    latest_commit = commits[-1].get("oid", "") if commits else ""

    reasons = []

    # 1. Merged check
    if state == "MERGED":
        reasons.append("PR successfully merged into base branch.")
        return "pass", reasons, data

    # 2. Closed without merge
    if state == "CLOSED":
        reasons.append("PR closed without being merged (rejected).")
        return "fail", reasons, data

    # 3. Review decision checks
    if review == "CHANGES_REQUESTED":
        reasons.append("Reviewers requested changes on this PR.")
        return "fail", reasons, data

    # 4. CI / Check runs analysis
    if checks:
        failed_checks = []
        pending_checks = []
        passed_checks = []

        for c in checks:
            name = c.get("name") or c.get("context") or "Check"
            conclusion = (c.get("conclusion") or c.get("state") or "").upper()
            status = (c.get("status") or "").upper()

            if conclusion in ("FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "ERROR"):
                failed_checks.append(name)
            elif status in ("IN_PROGRESS", "QUEUED", "PENDING") or conclusion in ("PENDING", ""):
                pending_checks.append(name)
            elif conclusion in ("SUCCESS", "NEUTRAL", "SKIPPED"):
                passed_checks.append(name)

        if failed_checks:
            reasons.append(f"CI check(s) failed: {', '.join(failed_checks)}")
            return "fail", reasons, data

        if pending_checks:
            reasons.append(f"Checks still in progress: {', '.join(pending_checks)}")
            return "pending", reasons, data

        if passed_checks and not failed_checks and not pending_checks:
            reasons.append(f"All {len(passed_checks)} CI checks passed.")
            return "pass", reasons, data

    # 5. If review approved without CI checks
    if review == "APPROVED":
        reasons.append("PR approved by reviewers.")
        return "pass", reasons, data

    reasons.append("PR is open with pending checks or awaiting review.")
    return "pending", reasons, data

def check_and_notify(recipient=None, dry_run=False, verbose=True):
    user = get_github_user()
    recipient = recipient or os.getenv("IMESSAGE_RECIPIENT")
    prs = fetch_user_prs()
    state_db = load_state()

    if verbose:
        print(f"🔍 Connected GitHub User : @{user}")
        print(f"📱 iMessage Recipient    : {recipient or '(None set - pass --recipient or set in .env)'}")
        print(f"📋 Found {len(prs)} PR(s) authored by @{user}")
        print("-" * 65)

    changes_found = 0

    for pr in prs:
        repo = pr.get("repository", {}).get("nameWithOwner", "unknown")
        num = pr.get("number")
        title = pr.get("title", "")
        url = pr.get("url", "")
        pr_key = f"{repo}#{num}"

        status, reasons, details = evaluate_pr_status(url)
        reason_str = "; ".join(reasons)

        pr_record = state_db.get(pr_key, {
            "last_status": None,
            "notified_status": None,
            "url": url,
            "title": title
        })

        last_notified = pr_record.get("notified_status")

        if verbose:
            badge = "⏳ PENDING"
            if status == "pass":
                badge = "✅ PASS"
            elif status == "fail":
                badge = "❌ FAIL"
            print(f"[{badge}] {pr_key}: '{title}'")
            print(f"       Status reason: {reason_str}")

        # Check if we should dispatch a notification
        if status in ("pass", "fail") and last_notified != status:
            changes_found += 1
            print(f"\n📢 PR Status Transition Detected for {pr_key} -> {status.upper()}!")
            
            # Generate appropriate message
            msg = generate_message(
                status=status,
                pr_number=num,
                pr_title=title,
                author=user,
                repo=repo,
                env="production"
            )

            print(f"💬 Generated iMessage:\n{'-'*40}\n{msg}\n{'-'*40}")

            if dry_run or not recipient:
                print(f"[DRY RUN] Would send iMessage to {recipient or '(no recipient configured)'}")
                pr_record["notified_status"] = status
                pr_record["notified_at"] = datetime.utcnow().isoformat()
            else:
                sent = send_imessage(recipient, msg)
                if sent:
                    pr_record["notified_status"] = status
                    pr_record["notified_at"] = datetime.utcnow().isoformat()

        pr_record["last_status"] = status
        pr_record["last_checked_at"] = datetime.utcnow().isoformat()
        state_db[pr_key] = pr_record

    save_state(state_db)
    if verbose:
        print("-" * 65)
        print(f"✨ Scan complete. State updated in {STATE_FILE.name}")
    return changes_found

def watch_loop(interval=60, recipient=None, dry_run=False):
    print(f"👀 Starting GitHub PR Watcher loop (polling every {interval}s)...")
    print(f"Press Ctrl+C to stop.")
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling GitHub PRs...")
            try:
                check_and_notify(recipient=recipient, dry_run=dry_run, verbose=True)
            except Exception as e:
                print(f"⚠️ Error during PR check: {str(e)}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping watcher loop.")

def daemon_start(interval=60, recipient=None):
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            print(f"⚠️ Daemon is already running (PID: {pid}).")
            return
        except OSError:
            pass # Stale pid

    cmd = [
        sys.executable, "-u", str(Path(__file__).resolve()),
        "--watch",
        "--interval", str(interval)
    ]
    if recipient:
        cmd.extend(["--recipient", recipient])

    log_path = Path(__file__).parent.parent / "pr_watcher.log"
    with open(log_path, "a") as log_file:
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            preexec_fn=os.setpgrp
        )
    PID_FILE.write_text(str(proc.pid))
    print(f"🚀 GitHub PR Watcher daemon started in background (PID: {proc.pid})")
    print(f"📄 Logs: {log_path}")

def daemon_stop():
    if not PID_FILE.exists():
        print("ℹ️ No active daemon found (no PID file).")
        return

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"🛑 Stopped GitHub PR Watcher daemon (PID: {pid}).")
    except ProcessLookupError:
        print("ℹ️ Daemon was not running (cleaned up stale PID file).")
    except Exception as e:
        print(f"❌ Error stopping daemon: {str(e)}")
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()

def daemon_status():
    if not PID_FILE.exists():
        print("⚪ GitHub PR Watcher daemon is NOT running.")
        return False

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        print(f"🟢 GitHub PR Watcher daemon is RUNNING (PID: {pid}).")
        return True
    except OSError:
        print("⚪ Daemon PID file exists, but process is dead.")
        PID_FILE.unlink()
        return False

def list_prs():
    user = get_github_user()
    prs = fetch_user_prs()
    print("=" * 80)
    print(f"🐙 GitHub PRs for @{user}")
    print("=" * 80)
    if not prs:
        print("No active PRs found.")
        return

    for pr in prs:
        repo = pr.get("repository", {}).get("nameWithOwner", "unknown")
        num = pr.get("number")
        title = pr.get("title", "")
        url = pr.get("url", "")
        status, reasons, _ = evaluate_pr_status(url)

        symbol = "⏳"
        if status == "pass":
            symbol = "✅"
        elif status == "fail":
            symbol = "❌"

        print(f"{symbol} [{repo} #{num}] {title}")
        print(f"   URL    : {url}")
        print(f"   Status : {status.upper()} ({'; '.join(reasons)})")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(
        description="Connect to GitHub, track your PRs, and send Shakespeare (fails) or Cold Guy (passes) iMessages."
    )
    parser.add_argument("--check", action="store_true", help="Scan your GitHub PRs once and notify for any state changes")
    parser.add_argument("--watch", action="store_true", help="Continuously poll GitHub PRs in the foreground")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds for --watch (default: 60)")
    parser.add_argument("--list", action="store_true", help="List all your active tracked GitHub PRs with CI/review status")
    parser.add_argument("--recipient", default=os.getenv("IMESSAGE_RECIPIENT"), help="iMessage recipient phone or email")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without sending actual iMessages")
    parser.add_argument("--daemon-start", action="store_true", help="Start watcher as a background daemon process")
    parser.add_argument("--daemon-stop", action="store_true", help="Stop background watcher daemon")
    parser.add_argument("--daemon-status", action="store_true", help="Check background watcher daemon status")
    parser.add_argument("--test", choices=["pass", "fail"], help="Test notification with a simulated PR")

    args = parser.parse_args()

    if args.daemon_start:
        daemon_start(interval=args.interval, recipient=args.recipient)
        return 0

    if args.daemon_stop:
        daemon_stop()
        return 0

    if args.daemon_status:
        daemon_status()
        return 0

    if args.test:
        user = get_github_user()
        msg = generate_message(
            status=args.test,
            pr_number=777,
            pr_title="feat: overhaul engine pipeline",
            author=user,
            repo="org/super-repo",
            env="production"
        )
        print(f"🧪 Testing {args.test.upper()} notification for @{user}:\n")
        print(msg)
        print("-" * 60)
        if args.recipient and not args.dry_run:
            send_imessage(args.recipient, msg)
        else:
            print(f"[DRY RUN] Pass --recipient to send real iMessage.")
        return 0

    if args.list:
        list_prs()
        return 0

    if args.watch:
        watch_loop(interval=args.interval, recipient=args.recipient, dry_run=args.dry_run)
        return 0

    # Default to check
    check_and_notify(recipient=args.recipient, dry_run=args.dry_run, verbose=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
