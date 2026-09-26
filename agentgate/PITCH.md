# How this wins the cash

The only cash prizes are from CodeRabbit:

- **$1,000**: best project **built with the Coding Agent**
- **$500**: best tool use of CodeRabbit, and you must post about it publicly
- **$300**: most Coding Agent feedback in their Discord

Main track (1st–3rd) pays Devin credits, and the project must be built with Jev. AgentGate does both: Jev decides, the CodeRabbit Coding Agent writes the fix.

## 90 seconds

> Agents write code faster than anyone can review it. AgentGate is the control plane. CodeRabbit's Coding Agent writes the patch. Jev is the only thing allowed to merge.
>
> The refund PR ships with a missing auth check. CodeRabbit flags it critical. Jev says fix, 95 percent. We hand that finding to the Coding Agent with `@coderabbitai autofix`. It pushes the patch. CodeRabbit reviews again and comes back clean. Jev says merge, 96 percent, risk 2.7. It merges.
>
> CodeRabbit is both the reviewer and the coder. Jev is the decision. Nothing merges while a critical finding is open.

## Before you demo live

1. Redeem coupon `JEVHACK1000` at coderabbit.ai → Billing → Usage → Agent usage → Redeem Coupon. You must be the workspace billing admin. No card.
2. Confirm the CodeRabbit GitHub App is installed on the demo repo.
3. Export `GITHUB_TOKEN`, `GITHUB_REPO`, and `JEV_API_KEY` on the laptop. Do not paste them into chat.
4. Live mode posts `@coderabbitai autofix` and waits up to 3 minutes for the Coding Agent's commit. That is the $1,000 qualifying action.
5. For the $500, post the demo publicly (X or LinkedIn) and include the repo link before judging.

Offline `python3 scripts/simple_demo.py` is the backup if the bot is slow. Say out loud that the live path is `@coderabbitai autofix`, and the offline patch is a stand-in.
