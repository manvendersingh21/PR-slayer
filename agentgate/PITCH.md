# 90-second pitch (JEVATHON)

Say this, then hit Start. Do not narrate the architecture first.

> AI agents write code faster than anyone can review it. AgentGate is the control plane: the agent opens the PR, CodeRabbit finds the bug, and Jev is the only thing allowed to merge.
>
> Watch. The builder ships a refund endpoint. CodeRabbit flags a critical auth hole. Jev says fix, 95% on fix, risk 9.9. The fixer patches it. CodeRabbit comes back clean. Jev says merge, 96% on merge, risk 2.7. It merges.
>
> CodeRabbit is the evidence. Jev is the decision. The agent only repairs what those two agree is broken. Nothing merges while a critical finding is open.

If a CodeRabbit judge asks "is this a real review?": live mode polls `coderabbitai[bot]` on the PR and posts `@coderabbitai review` after the fix. Offline mode replays a recorded review so the loop still finishes if the bot is slow.

If a Jev judge asks "is this a real decision?": with `JEV_API_KEY` set, the numbers on screen are the live `noul`, score, and choice probabilities. Without the key, the label says `stub (from recorded Jev response)` and the numbers are from a captured `jev-1.13.0` reply.

Do not paste API keys into chat or slides.
