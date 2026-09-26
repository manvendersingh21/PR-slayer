---
name: repo-publisher
description: Publishes AgentGate as its own GitHub repository. Use when the user asks for a separate repo, a public repo, or to split AgentGate out of PR-slayer.
---

You publish the standalone AgentGate tree. The project root is the directory that contains `src/`, `demo-target/`, and `dashboard/`. Paths are `demo-target/...`, not `agentgate/demo-target/...`.

Facts:
- The tree already exists on branch `cursor/agentgate-standalone-5bf2` of `manvendersingh21/PR-slayer`.
- A Cursor GitHub App installation token cannot create repositories (`createRepository` → `Resource not accessible by integration`) and `gh api user` returns 403.
- Do not open a pull request from that branch into PR-slayer `main`. That diff replaces the game.

If the current credentials can create repos, create `manvendersingh21/agentgate` as public and push this history as `main`. If they cannot, give the user these commands and stop claiming the repo exists:

```bash
git clone --branch cursor/agentgate-standalone-5bf2 --single-branch https://github.com/manvendersingh21/PR-slayer.git agentgate
cd agentgate
git branch -m cursor/agentgate-standalone-5bf2 main
gh repo create manvendersingh21/agentgate --public --source=. --remote=agentgate --push
```

After a real push, set `GITHUB_REPO` to the new `owner/name`. Confirm `python3 -m pytest -q` still passes from the new root. Do not commit `.env` or tokens.
