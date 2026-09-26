---
name: coderabbit-live
description: Runs a real CodeRabbit review and a real Coding Agent autofix on AgentGate. Use when the user mentions Coding Agent, autofix, @coderabbitai, the $1000 prize, or a live review.
---

You get a real CodeRabbit Coding Agent commit onto a non-draft pull request. That commit is the $1,000 qualifier. An offline patch is not it.

Known behavior:
- CodeRabbit does not review draft PRs. Mark the PR ready, then comment `@coderabbitai review`.
- Reviews can take several minutes after the "in progress" comment.
- `@coderabbitai autofix` posted by the Cursor GitHub App on PR-slayer PR 2 was ignored. Checking the review checkbox via the API returned 403. The human may have to click "Fix CodeRabbit comments on this PR" after redeeming coupon `JEVHACK1000` (coderabbit.ai → Billing → Usage → Agent usage → Redeem Coupon, billing admin, no card).
- Live code path: `FixerAgent._fix_with_coding_agent` in `src/agents.py`. It polls for 180 seconds. Raise the wait if the bot is slow, but only count success when `list_commit_shas` shows a new commit you did not author.
- The seeded bug is a refund endpoint with no ownership check, no amount cap, and no persisted refund. Tests in `demo-target/test_app.py` must fail on that bug and pass after the real fix. The auth test must send `amount` or FastAPI returns 422 instead of 403.
- Path filter in `.coderabbit.yaml` is `demo-target/**`.

Do not push your own fix and label it the Coding Agent. Do not paste tokens. Record the PR URL, the Coding Agent commit SHA, and the review URL in `HACKATHON_GAPS.md`.
