# PR Slayer

**A tiny browser game where you defeat a sentient PR deadline by rage-typing, integrated with GitHub and iMessage.**

Built for the NERDCONF Fun Build track.

## Main interaction
- Type fast to damage the PR DEADLINE boss.
- Fast typing builds a combo and increases damage.
- Spacebar lands a mini-critical hit.
- Enter unleashes **SEND IT** for a heavy hit.
- Backspace heals the boss, because editing has consequences.
- The boss taunts you, watches your cursor, shakes on crits, and explodes into confetti when defeated.

## Run locally
No dependencies.

1. Download the folder.
2. Open `index.html` in Chrome, Safari, Firefox, or Edge.
3. Click **BEGIN POOR DECISIONS**.
4. Type like your submission is due in 90 seconds.

## Deploy
This is a single static HTML file, so it can be deployed directly to:
- GitHub Pages
- Netlify
- Vercel
- Cloudflare Pages

No backend, API keys, database, or account required.

## Suggested 20-second demo
1. Open the page and click **BEGIN POOR DECISIONS**.
2. Start typing slowly to show normal damage.
3. Rage-type to build the combo meter.
4. Hit **Enter** to trigger **SEND IT**.
5. Press Backspace once so the boss heals and insults you.
6. Finish the boss and show the result grade/confetti.

## Hardware requirements
Any laptop or desktop with a keyboard and modern web browser.

## Privacy
Everything runs locally in the browser. No typed text is sent anywhere or stored.

---

## 🎭 GitHub PR iMessage Gatekeeper & Live Tracker

Automatically connects to your **GitHub Account** (via `gh` CLI) to keep track of your Pull Requests across all repositories and dispatch iMessages directly to your Mac:
- ❌ **If your PR fails (CI checks fail or changes requested)**: You get roasted by a theatrical **William Shakespeare** mocking your code, ancestry, and inability to write tests.
- ✅ **If your PR passes / is approved**: An ice-cold engineer hits you with: ***"You could've done better on that PR."*** followed by an emotionless nod to merge and get back to work.
- 💾 **Smart State Tracking**: Stores status in `.pr_tracker_state.json` to prevent duplicate notifications.

### 1. Track Your GitHub PRs
Connects seamlessly to your logged-in GitHub CLI account (`@manvendersingh21`):

```bash
# List all your active GitHub PRs with live CI / review status:
./scripts/test_notification.sh list

# Scan all your PRs once and notify for any status transitions:
./scripts/test_notification.sh check

# Start continuous live polling in foreground (checks every 60s):
./scripts/test_notification.sh watch

# Run the watcher continuously in the background as a daemon:
./scripts/test_notification.sh daemon-start
./scripts/test_notification.sh daemon-status
./scripts/test_notification.sh daemon-stop
```

### 2. Manual Testing & Preview
```bash
# Preview Shakespeare failure roast:
./scripts/test_notification.sh fail

# Preview Cold Guy approval ("You could've done better on that PR"):
./scripts/test_notification.sh pass

# Send real iMessage directly to your phone:
./scripts/test_notification.sh fail +1XXXXXXXXXX
./scripts/test_notification.sh pass +1XXXXXXXXXX
```

### 3. Configuration (`.env`)
Store your phone number or Apple ID email in `.env`:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
IMESSAGE_RECIPIENT="+1XXXXXXXXXX"
```

### 4. Interactive In-Browser PR Monitor
1. Open `index.html` in your browser.
2. Click the **🎭 PR iMessage** button in the top bar.
3. Select any of your real GitHub PRs (e.g. `chatgpt-clone #145`, `Datadecor-website #9`) from the quick-picker chips to preview live messages, copy CLI commands, or dispatch test iMessages!

### 5. CI/CD & GitHub Actions Integration
A ready-to-use GitHub Actions workflow is provided in [`.github/workflows/production_deploy.yml`](.github/workflows/production_deploy.yml).
- **On a macOS runner**: Invokes `scripts/pr_imessage_notifier.py` natively via AppleScript.
- **On Linux / Cloud runners**: Run `python3 scripts/webhook_server.py` on your Mac and pass your webhook URL into repository secrets.
