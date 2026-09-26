#!/usr/bin/env python3
"""
Simple hardcoded demo that always works for presentation
"""
import time
from datetime import datetime, timezone

print("\n" + "="*60)
print("AgentGate - Autonomous PR Safety Loop")
print("="*60 + "\n")

print("Mode: OFFLINE DEMO\n")

print("="*60)
print("PR #123 — Add refund endpoint")
print("="*60 + "\n")

# Builder
print("✨ Builder Agent")
print("   Status: ✅ Complete")
print("   Branch: agentgate/add-refund-endpoint")
print()
time.sleep(1)

# Tests
print("🧪 Tests")
print("   Status: ✅ All tests pass")
print()
time.sleep(1)

# First Review
print("🔍 CodeRabbit Review (Attempt 1)")
print("   Status: 🔴 1 Critical Issue")
print("   Finding: Missing authorization check - Any user can refund any payment")
print()
time.sleep(1)

# Jev Decision 1
print("🤖 Jev Decision")
print("   Merge Safe: NO")
print("   Risk Score: 9.2 / 10")
print("   Confidence: 95.0%")
print("   Action: FIX")
print()
time.sleep(1)

# Fixer
print("🔧 Fixer Agent")
print("   Status: ✅ Applied security fixes")
print("   - Added user ownership verification")
print("   - Added refund amount validation")
print("   - Added double-refund prevention")
print()
time.sleep(1)

# Second Review
print("🔍 CodeRabbit Review (Attempt 2)")
print("   Status: 🟢 Clean")
print("   Findings: 0")
print()
time.sleep(1)

# Jev Decision 2
print("🤖 Jev Decision")
print("   Merge Safe: YES")
print("   Risk Score: 1.1 / 10")
print("   Confidence: 98.0%")
print("   Action: MERGE")
print()
time.sleep(1)

# Merge
print("🎉 Merge")
print("   Status: ✅ PR MERGED")
print()

print("="*60)
print("✅ Demo Complete - PR merged safely!")
print("="*60)
print()
print("Summary:")
print("  Attempts: 2")
print("  Initial Risk: 9.2/10")
print("  Final Risk: 1.1/10")
print("  Result: SAFE TO MERGE")
