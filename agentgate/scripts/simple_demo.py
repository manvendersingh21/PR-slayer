#!/usr/bin/env python3
"""
Simple terminal demo using REAL orchestrator and adapters
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapters import create_adapters
from src.agents import BuilderAgent, FixerAgent
from src.orchestrator import Orchestrator


def format_event(event):
    """Format event for pretty terminal output"""
    icons = {
        "builder_complete": "✨",
        "tests_complete": "🧪",
        "review_complete": "🔍",
        "decision_complete": "🤖",
        "fix_complete": "🔧",
        "merge_complete": "🎉"
    }
    
    icon = icons.get(event.type, "•")
    
    if event.type == "builder_complete":
        print(f"\n{icon} Builder Agent")
        print(f"   Status: ✅ Complete")
        print(f"   PR: #{event.pr_number}")
    
    elif event.type == "tests_complete":
        status = "✅ Pass" if event.data.get("passed") else "❌ Fail"
        print(f"\n{icon} Tests")
        print(f"   Status: {status}")
    
    elif event.type == "review_complete":
        critical = event.data.get("critical_count", 0)
        total = event.data.get("findings_count", 0)
        if critical > 0:
            print(f"\n{icon} CodeRabbit Review")
            print(f"   Status: 🔴 {critical} Critical Issue{'s' if critical > 1 else ''}")
            findings = event.data.get("findings", [])
            for f in findings[:1]:  # Show first critical
                if f["severity"] == "critical":
                    print(f"   Finding: {f['message']}")
        else:
            print(f"\n{icon} CodeRabbit Review")
            print(f"   Status: 🟢 Clean")
    
    elif event.type == "decision_complete":
        decision = event.data
        safe = "YES" if decision.get("merge_safe") else "NO"
        risk = decision.get("risk", 0)
        conf = decision.get("confidence", 0)
        action = decision.get("action", "unknown").upper()
        
        print(f"\n{icon} Jev Decision")
        print(f"   Merge Safe: {safe}")
        print(f"   Risk Score: {risk:.1f} / 10")
        print(f"   Confidence: {conf:.1f}%")
        print(f"   Action: {action}")
    
    elif event.type == "fix_complete":
        print(f"\n{icon} Fixer Agent")
        print(f"   Status: ✅ Applied fixes")
    
    elif event.type == "merge_complete":
        print(f"\n{icon} Merge")
        print(f"   Status: ✅ PR MERGED")


def main():
    print("\n" + "="*60)
    print("AgentGate - Autonomous PR Safety Loop")
    print("="*60 + "\n")
    
    # Setup
    repo_path = os.getenv("REPO_PATH", "/workspace")
    os.environ.pop("GITHUB_TOKEN", None)  # Force offline
    os.environ.pop("JEV_API_KEY", None)
    os.environ.pop("TYPESAFE_API_KEY", None)
    
    # Create adapters
    adapters = create_adapters(repo_path)
    print(f"Mode: {adapters['mode'].upper()}\n")
    
    # Create agents
    builder = BuilderAgent(adapters["llm"], adapters["github"], repo_path)
    fixer = FixerAgent(adapters["llm"], repo_path)
    
    # Event callback
    events = []
    def log_event(event):
        events.append(event)
        format_event(event)
    
    # Create orchestrator
    orchestrator = Orchestrator(
        builder=builder,
        fixer=fixer,
        github=adapters["github"],
        coderabbit=adapters["coderabbit"],
        jev=adapters["jev"],
        repo_path=repo_path,
        event_callback=log_event
    )
    
    # Run loop
    issue = "Create a refund endpoint"
    branch = "agentgate/demo-refund-endpoint"
    
    print("="*60)
    print("PR — Add refund endpoint")
    print("="*60)
    
    result = orchestrator.run_loop(issue, branch)
    
    # Summary
    print("\n" + "="*60)
    if result["success"]:
        print("✅ Demo Complete - PR merged safely!")
    else:
        print("⚠️  Demo Complete - Human review required")
    print("="*60)
    print()
    print("Summary:")
    print(f"  Attempts: {result['attempts']}")
    if result.get('decision'):
        print(f"  Final Risk: {result['decision']['risk']:.1f}/10")
        print(f"  Result: {result['decision']['action'].upper()}")
    
    return 0 if result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
