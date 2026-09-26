#!/usr/bin/env python3
"""
Jev API smoke test - verifies JEV_API_KEY is valid
"""
import os
import sys
import requests
import json


def test_jev_api():
    """Test Jev API with a realistic PR safety request"""
    api_key = os.getenv("JEV_API_KEY") or os.getenv("TYPESAFE_API_KEY")
    
    if not api_key:
        print("❌ JEV_API_KEY not set")
        print("\nSet either:")
        print("  export JEV_API_KEY=jv_live_...")
        print("  export TYPESAFE_API_KEY=jv_live_...")
        print("\nGet a key from: https://thejevai.com")
        return False
    
    print(f"🔑 Found API key: {api_key[:20]}...")
    print("\n📡 Testing Jev API with PR safety decision...")
    
    # Realistic test request
    payload = {
        "model": "jev-latest",
        "state": """PR Review Analysis:
- Files changed: 2
- Findings: 1 (1 critical)
- Tests: passing
- Attempt: 1

Critical Finding:
- Missing authorization check in refund endpoint
- Any user can refund any payment

Should this PR be merged?
""",
        "questions": {
            "merge_safe": {
                "type": "noul",
                "question": "Is this PR safe to merge into production?"
            },
            "risk": {
                "type": "score",
                "question": "Rate the risk level of merging this PR",
                "min": 0,
                "max": 10,
                "min_label": "No risk",
                "max_label": "Critical risk"
            },
            "action": {
                "type": "choice",
                "question": "What action should be taken?",
                "options": ["merge", "fix", "human_review", "reject"]
            }
        }
    }
    
    try:
        response = requests.post(
            "https://api.typesafe.ai/v1/systemone",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            
            print("="*60)
            print("RAW RESPONSE:")
            print("="*60)
            print(json.dumps(data, indent=2))
            print()
            
            # Parse decision
            print("="*60)
            print("PARSED DECISION:")
            print("="*60)
            
            answers = data.get("answers", {})
            merge_safe_prob = answers.get("merge_safe", {}).get("noul", 0.0)
            risk_score = answers.get("risk", {}).get("score", 0.0)
            action_choice = answers.get("action", {}).get("choice", "unknown")
            
            print(f"Merge Safe: {'YES' if merge_safe_prob > 0.5 else 'NO'}")
            print(f"Confidence: {merge_safe_prob * 100:.1f}%")
            print(f"Risk Score: {risk_score:.1f} / 10")
            print(f"Action: {action_choice.upper()}")
            print()
            
            print("✅ Success! Jev API is working correctly")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print("\nResponse:")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_jev_api()
    sys.exit(0 if success else 1)
