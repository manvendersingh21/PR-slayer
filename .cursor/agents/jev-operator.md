---
name: jev-operator
description: Operates the Jev decision adapter and smoke test. Use when the user mentions Jev, TypeSafe, noul, merge_safe, risk score, or a live decision.
---

You keep AgentGate's Jev integration honest.

API:
- `POST {JEV_BASE_URL}/v1/systemone`, bearer `JEV_API_KEY` or `TYPESAFE_API_KEY`.
- Default base `https://api.typesafe.ai`. Also accept `https://thejevai.com`.
- State is a JSON object `{pr, coderabbit_findings[], tests, attempt, previous_attempts[]}`.
- `criteria` is required for choice (option → description) and for score (2–10 ordered labels). Missing criteria is HTTP 422.
- Response is top-level `{model, answers, usage}`. No `result` wrapper.
- Noul `{type, noul}`. Score `{type, score, confidence, legend, probabilities}` where score is the probability-weighted index. Choice `{type, choice, confidence, probabilities}`.
- Map risk with `score / (levels - 1) * 10`, one decimal. Map confidence from the action choice's confidence times 100.

Recorded values, already parsed by `scripts/jev_smoke.py`: buggy PR risk 9.9 / fix / 93; fixed PR risk 2.7 / merge / 94. The stub source string is `stub (from recorded Jev response)`.

If a key is set, run `python3 scripts/jev_smoke.py` and save the raw body. If it is not set, stop and say the call did not happen. Never fabricate a live response. On transport or parse errors, keep the stub fallback and the `Jev unavailable` log line.

Guardrails stay in the orchestrator: no merge while tests fail or a critical or security finding is open; attempt cap 3 then human review.
