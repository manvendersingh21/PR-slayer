#!/usr/bin/env python3
"""
PR iMessage Notifier:
- If a PR fails in production: Sends an iMessage mocking you like William Shakespeare.
- If a PR passes / is approved: Sends an iMessage like a really cold guy congratulating you ("Your PR has been approved.").
"""

import sys
import os
import argparse
import random
import subprocess
import platform
from pathlib import Path

# Try loading .env if available
def load_dotenv():
    env_paths = [Path('.env'), Path('../.env'), Path(__file__).parent.parent / '.env']
    for p in env_paths:
        if p.exists():
            with open(p, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
            break

load_dotenv()

SHAKESPEARE_FAILURES = [
    (
        "🎭 HARK, THOU PLAGUE OF PRODUCTION! 🎭\n\n"
        "Alas, what black and hideous pestilence hath thy clumsy fingers unleashed upon the sacred servers?! "
        "Thou hast thrust thy scurvy patch into Holy Production, and lo—the temple lieth shattered, "
        "the logs vomit crimson tears, and the SREs weep into the abyss!\n\n"
        "Thou whoreson, beetle-headed, beslubbering malt-worm! Didst thou dare merge with neither test nor shame? "
        "Thou art a boil, a plague sore, an embossed carbuncle upon git history! "
        "May thy stack traces haunt thee till the end of days. Revert thy cursed branch and crawl into exile, "
        "for thy Pull Request hath perished most foully!"
    ),
    (
        "⚡ BY APOLLO, WHAT MONSTROUS FOLLY IS THIS?! ⚡\n\n"
        "O villainous knave of the terminal! Thou didst swear thy code was sound, yet upon the anvil of Production "
        "it splintered like wanton glass! Thou clouted, rump-fed hedge-pig!\n\n"
        "The uptime hath plummeted into Tartarus, and thy name is cursed from engineering even unto leadership! "
        "Was thy brain curdled with sour grog when thou didst approve thine own catastrophe?! "
        "Fie, fie upon thee, thou lump of foul deformity! Go wash thy hands in tears and rollback ere the CTO striketh thee down!"
    ),
    (
        "🗡️ DISASTER MOST FOUL AND UNNATURAL! 🗡️\n\n"
        "Hear me, thou spongy, milk-livered miscreant! Thou hast plunged the poisoned dagger of ignorance "
        "straight into the beating heart of Production! The database groaneth, the pods perish like autumn leaves, "
        "and thy pull request drowneth in its own ignominy!\n\n"
        "A pox upon thy commits, thou rank rampallian, thou fustilarian! "
        "More poisonous art thou than the adder. Go hide thy disgraced visage, thou illiterate codpiece, "
        "and speak no more of deployment till thou hast learned the humble craft of unit tests!"
    ),
    (
        "💀 WOE UNTO THE REALM, PRODUCTION BURNETH! 💀\n\n"
        "What wretched abomination hast thou hatched, thou knotty-pated fool?! "
        "Production collapseth under the insolence of thy pull request! "
        "Thou art unfit for the company of developers, nay, unfit even for the staging cluster!\n\n"
        "Thou gorbellied, flap-ear'd ruffian! Thine errors cry out to the high heavens for vengeance. "
        "Thy build hath choked upon its own hubris and perished in the dark. Repent, thou scurvy knave, "
        "and pray the git log forgetteth thy sins!"
    ),
    (
        "🥀 THOU DULL UNVARNISHED IDIOT OF THE REPO! 🥀\n\n"
        "Stand accused, thou churlish, sheep-biting coxcomb! Thou didst look upon Production and think, "
        "'Lo, let me inflict my broken logic upon the innocent users!' And now, behold: 500s across the kingdom, "
        "the monitors scream in agony, and thy pull request lieth dead in the ditch!\n\n"
        "I would challenge thee to a battle of wits, but I perceive thou art completely unarmed. "
        "Roll back thy foul catastrophe this instant, thou bawdy barnacle, and beg mercy upon thy bended knees!"
    )
]

COLD_GUY_PASSES = [
    (
        "Your PR has been approved.\n\n"
        "You could've done better on that PR. The production build passed, but merely meeting the bare minimum expectation is not an achievement. "
        "Merge it and get back to work."
    ),
    (
        "Your PR has been approved.\n\n"
        "You could've done better on that PR. Production didn't crash. Cool. That was literally your job. "
        "Don't expect a medal. Next ticket is waiting."
    ),
    (
        "Your PR has been approved.\n\n"
        "Honestly? You could've done better on that PR. The diff is bloated and the commit history is a mess. "
        "Passed, barely. Don't let it inflate your ego. Merge and move on."
    ),
    (
        "Your PR has been approved.\n\n"
        "You could've done better on that PR. The bar was on the floor and you managed not to trip over it. "
        "Ship it. Don't text back."
    ),
    (
        "Your PR has been approved.\n\n"
        "You could've done better on that PR. Took you long enough. It works, but we have five more blockers in the sprint. "
        "Back to your desk."
    ),
    (
        "Your PR has been approved.\n\n"
        "You could've done better on that PR. Adequate at best. Nothing to boast about. "
        "Merge before I find another nitpick."
    ),
    (
        "Your PR has been approved.\n\n"
        "You could've done better on that PR. It's green, but nobody is impressed. "
        "Close the ticket."
    )
]

def generate_message(status: str, pr_number=None, pr_title=None, author=None, repo=None, env="production"):
    is_fail = status.lower() in ("fail", "failure", "failed", "error", "rejected")
    
    if is_fail:
        base = random.choice(SHAKESPEARE_FAILURES)
        details = []
        if repo:
            details.append(f"📦 {repo}")
        if pr_number:
            details.append(f"📜 PR #{pr_number}")
        if pr_title:
            details.append(f"🏷️ Title: '{pr_title}'")
        if author:
            details.append(f"👤 Culprit: {author}")
        if env:
            details.append(f"🏰 Realm: {env.upper()}")
        
        if details:
            header = " — ".join(details)
            return f"{header}\n\n{base}"
        return base
    else:
        base = random.choice(COLD_GUY_PASSES)
        extras = []
        if repo:
            extras.append(f"{repo}")
        if pr_number:
            extras.append(f"PR #{pr_number}")
        if pr_title:
            extras.append(f"'{pr_title}'")
        if env and env.lower() != "production":
            extras.append(f"env: {env}")
            
        if extras:
            prefix = f"[{' | '.join(extras)}]\n"
            return f"{prefix}{base}"
        return base

def send_imessage(recipient: str, message: str) -> bool:
    if platform.system() != "Darwin":
        print(f"⚠️  Not on macOS (detected {platform.system()}). iMessage requires macOS with Messages.app configured.")
        print(f"Would send to {recipient}:\n---\n{message}\n---")
        return False

    applescript = '''
    on run argv
        set targetRecipient to item 1 of argv
        set messageText to item 2 of argv
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            try
                set targetBuddy to buddy targetRecipient of targetService
                send messageText to targetBuddy
                return "SUCCESS"
            on error err1
                try
                    set targetBuddy to participant targetRecipient of targetService
                    send messageText to targetBuddy
                    return "SUCCESS_PARTICIPANT"
                on error err2
                    try
                        send messageText to buddy targetRecipient
                        return "SUCCESS_DIRECT"
                    on error err3
                        error "Messages Error: " & err1 & " | " & err2 & " | " & err3
                    end try
                end try
            end try
        end tell
    end run
    '''

    try:
        res = subprocess.run(
            ["osascript", "-", recipient, message],
            input=applescript,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ iMessage successfully sent to {recipient}!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to send iMessage via AppleScript:")
        print(e.stderr.strip())
        print("\n💡 Troubleshooting Tips:")
        print("  1. Verify the recipient phone number (with country code, e.g. +1234567890) or Apple ID email.")
        print("  2. Ensure Messages.app is signed into iMessage.")
        print("  3. Check macOS Privacy & Security -> Automation to ensure Terminal/Python has permission to control Messages.")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Send dramatic Shakespearean insults for failed PRs or cold deadpan approvals for passed PRs via iMessage."
    )
    parser.add_argument(
        "--status",
        choices=["fail", "failure", "failed", "pass", "passed", "success", "approved", "rejected"],
        required=True,
        help="PR outcome: fail/failure/rejected OR pass/passed/success/approved"
    )
    parser.add_argument(
        "--env",
        default="production",
        help="Deployment environment (default: production)"
    )
    parser.add_argument(
        "--recipient",
        default=os.getenv("IMESSAGE_RECIPIENT"),
        help="Recipient phone number (e.g. +1234567890) or Apple ID email. Can also be set via IMESSAGE_RECIPIENT env var or .env."
    )
    parser.add_argument("--repo", help="Repository name (e.g. 'owner/repo')")
    parser.add_argument("--pr-number", help="Pull request number (e.g. 42)")
    parser.add_argument("--pr-title", help="Pull request title (e.g. 'feat: optimize garbage collection')")
    parser.add_argument("--pr-author", help="Pull request author handle or name")
    parser.add_argument("--dry-run", action="store_true", help="Print the generated message without sending")
    parser.add_argument("--custom-message", help="Override the generated message")

    args = parser.parse_args()

    # Determine message
    if args.custom_message:
        message = args.custom_message
    else:
        message = generate_message(
            status=args.status,
            pr_number=args.pr_number,
            pr_title=args.pr_title,
            author=args.pr_author,
            repo=args.repo,
            env=args.env
        )

    print("=" * 60)
    print(f"🚀 Environment : {args.env}")
    print(f"📊 Status      : {args.status.upper()}")
    print(f"📱 Recipient   : {args.recipient or '(None specified)'}")
    print("=" * 60)
    print("💬 Message Content:")
    print(message)
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN] Message generated successfully. No iMessage sent.")
        return 0

    if not args.recipient:
        print("\n⚠️  No recipient specified! Use --recipient '+1XXXXXXXXXX' or set IMESSAGE_RECIPIENT in .env")
        print("To test without sending, pass --dry-run")
        return 1

    success = send_imessage(args.recipient, message)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
