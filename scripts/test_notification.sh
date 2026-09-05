#!/usr/bin/env bash
# Quick test and runner script for GitHub PR iMessage Notifier & Watcher

ACTION="${1:-list}"
RECIPIENT="${2:-}"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

case "$ACTION" in
  list)
    echo "🐙 Listing your active GitHub PRs..."
    python3 "$DIR/github_pr_watcher.py" --list
    ;;
  check)
    echo "🔍 Checking your GitHub PRs for status changes..."
    if [ -n "$RECIPIENT" ]; then
      python3 "$DIR/github_pr_watcher.py" --check --recipient "$RECIPIENT"
    else
      python3 "$DIR/github_pr_watcher.py" --check
    fi
    ;;
  watch)
    echo "👀 Starting GitHub PR Watcher in foreground (Ctrl+C to stop)..."
    if [ -n "$RECIPIENT" ]; then
      python3 "$DIR/github_pr_watcher.py" --watch --recipient "$RECIPIENT"
    else
      python3 "$DIR/github_pr_watcher.py" --watch
    fi
    ;;
  daemon-start)
    echo "🚀 Starting GitHub PR Watcher background daemon..."
    if [ -n "$RECIPIENT" ]; then
      python3 "$DIR/github_pr_watcher.py" --daemon-start --recipient "$RECIPIENT"
    else
      python3 "$DIR/github_pr_watcher.py" --daemon-start
    fi
    ;;
  daemon-stop)
    python3 "$DIR/github_pr_watcher.py" --daemon-stop
    ;;
  daemon-status)
    python3 "$DIR/github_pr_watcher.py" --daemon-status
    ;;
  fail)
    echo "🎭 Testing Shakespeare Failure Insult..."
    if [ -z "$RECIPIENT" ]; then
      python3 "$DIR/pr_imessage_notifier.py" --status fail --pr-number 404 --pr-title "Emergency bypass of unit tests" --pr-author "You" --dry-run
    else
      python3 "$DIR/pr_imessage_notifier.py" --status fail --pr-number 404 --pr-title "Emergency bypass of unit tests" --pr-author "You" --recipient "$RECIPIENT"
    fi
    ;;
  pass)
    echo "❄️  Testing Cold Guy Approval ('You could've done better')..."
    if [ -z "$RECIPIENT" ]; then
      python3 "$DIR/pr_imessage_notifier.py" --status pass --pr-number 200 --pr-title "Clean architectural refactor" --pr-author "You" --dry-run
    else
      python3 "$DIR/pr_imessage_notifier.py" --status pass --pr-number 200 --pr-title "Clean architectural refactor" --pr-author "You" --recipient "$RECIPIENT"
    fi
    ;;
  *)
    echo "Usage: $0 [list|check|watch|daemon-start|daemon-stop|daemon-status|fail|pass] [optional_recipient]"
    echo ""
    echo "Examples:"
    echo "  $0 list                       # List all your active GitHub PRs"
    echo "  $0 check                      # Scan PRs once and notify on changes"
    echo "  $0 watch                      # Foreground polling loop"
    echo "  $0 daemon-start               # Run watcher continuously in background"
    echo "  $0 daemon-stop                # Stop background watcher"
    echo "  $0 pass                       # Dry run Cold Guy approval"
    echo "  $0 fail                       # Dry run Shakespeare insult"
    echo "  $0 pass +1XXXXXXXXXX          # Send real iMessage approval"
    echo "  $0 fail +1XXXXXXXXXX          # Send real iMessage insult"
    ;;
esac
