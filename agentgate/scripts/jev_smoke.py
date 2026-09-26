#!/usr/bin/env python3
"""
Jev API smoke test with VERIFIED real schema
Tests against captured real API responses
"""
import os
import sys
import requests
import json


# Real captured responses from verified Jev API calls
REAL_RESPONSE_BUGGY_PR = {
    "model": "jev-1.13.0",
    "answers": {
        "merge_safe": {"type": "noul", "noul": 0.02},
        "risk": {
            "type": "score",
            "score": 3.96,
            "confidence": 0.96,
            "legend": {"0": "None", "1": "Low", "2": "Moderate", "3": "High", "4": "Severe"},
            "probabilities": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.04, "4": 0.96}
        },
        "action": {
            "type": "choice",
            "choice": "fix",
            "confidence": 0.93,
            "probabilities": {"fix": 0.95, "merge": 0.0, "reject": 0.0, "human_review": 0.05}
        }
    },
    "usage": {"input_tokens": 603, "output_tokens": 76}
}

REAL_RESPONSE_FIXED_PR = {
    "model": "jev-1.13.0",
    "answers": {
        "merge_safe": {"type": "noul", "noul": 0.84},
        "risk": {
            "type": "score",
            "score": 1.08,
            "confidence": 0.88,
            "legend": {"0": "None", "1": "Low", "2": "Moderate", "3": "High", "4": "Severe"},
            "probabilities": {"0": 0.04, "1": 0.86, "2": 0.09, "3": 0.01, "4": 0.0}
        },
        "action": {
            "type": "choice",
            "choice": "merge",
            "confidence": 0.94,
            "probabilities": {"human_review": 0.04, "merge": 0.96, "fix": 0.0, "reject": 0.0}
        }
    },
    "usage": {"input_tokens": 609, "output_tokens": 76}
}


def parse_jev_response(data):
    """Parse Jev response using verified schema"""
    answers = data.get("answers", {})
    
    # Parse merge_safe
    noul = answers.get("merge_safe", {}).get("noul", 0.5)
    merge_safe = noul >= 0.5
    
    # Parse risk with legend mapping
    risk_data = answers.get("risk", {})
    risk_score = risk_data.get("score", 0.0)
    risk_legend = risk_data.get("legend", {})
    num_levels = len(risk_legend)
    
    # Map to 0-10: score / (levels-1) * 10
    if num_levels > 1:
        risk_0_10 = (risk_score / (num_levels - 1)) * 10
    else:
        risk_0_10 = risk_score
    
    # Parse action
    action_data = answers.get("action", {})
    action_choice = action_data.get("choice", "unknown")
    action_confidence = action_data.get("confidence", 0.0)
    action_probs = action_data.get("probabilities", {})
    
    return {
        "merge_safe": merge_safe,
        "confidence": action_confidence * 100,
        "risk_0_10": round(risk_0_10, 1),
        "action": action_choice,
        "noul": noul,
        "raw_score": risk_score,
        "probabilities": action_probs
    }


def test_parser_on_real_captures():
    """Test parser against real captured responses"""
    print("="*60)
    print("TESTING PARSER ON REAL CAPTURED RESPONSES")
    print("="*60)
    
    print("\n1. Buggy PR Response (1 critical + 1 major, 1 failing test):")
    print("-" * 60)
    parsed = parse_jev_response(REAL_RESPONSE_BUGGY_PR)
    print(f"Merge Safe: {'YES' if parsed['merge_safe'] else 'NO'} (noul={parsed['noul']:.2f})")
    print(f"Risk: {parsed['risk_0_10']:.1f}/10 (raw score={parsed['raw_score']:.2f})")
    print(f"Action: {parsed['action'].upper()}")
    print(f"Confidence: {parsed['confidence']:.1f}%")
    print(f"Probabilities: {json.dumps(parsed['probabilities'], indent=2)}")
    
    print("\n2. Fixed PR Response (no findings, 5/5 tests, attempt 2):")
    print("-" * 60)
    parsed = parse_jev_response(REAL_RESPONSE_FIXED_PR)
    print(f"Merge Safe: {'YES' if parsed['merge_safe'] else 'NO'} (noul={parsed['noul']:.2f})")
    print(f"Risk: {parsed['risk_0_10']:.1f}/10 (raw score={parsed['raw_score']:.2f})")
    print(f"Action: {parsed['action'].upper()}")
    print(f"Confidence: {parsed['confidence']:.1f}%")
    print(f"Probabilities: {json.dumps(parsed['probabilities'], indent=2)}")
    print()


def test_jev_api():
    """Test real Jev API with verified schema"""
    api_key = os.getenv("JEV_API_KEY") or os.getenv("TYPESAFE_API_KEY")
    
    if not api_key:
        print("❌ JEV_API_KEY not set")
        print("\nSet either:")
        print("  export JEV_API_KEY=jv_live_...")
        print("  export TYPESAFE_API_KEY=jv_live_...")
        print("\nGet a key from: https://thejevai.com")
        return False
    
    base_url = os.getenv("JEV_BASE_URL", "https://api.typesafe.ai")
    url = f"{base_url}/v1/systemone"
    
    print(f"🔑 Found API key: {api_key[:20]}...")
    print(f"📡 Testing Jev API at: {url}")
    print()
    
    # Test request with VERIFIED schema
    payload = {
        "model": "jev-latest",
        "state": {
            "pr": {"number": 123, "files_changed": 2},
            "coderabbit_findings": [
                {
                    "severity": "critical",
                    "category": "security",
                    "file": "app.py",
                    "line": 75,
                    "message": "Missing authorization check in refund endpoint"
                }
            ],
            "tests": {"passing": False, "failed_count": 1},
            "attempt": 1,
            "previous_attempts": []
        },
        "questions": {
            "merge_safe": {
                "type": "noul",
                "instructions": "Is this pull request safe to merge as-is?",
                "criteria": {
                    "true": "No open critical/security issues and tests pass",
                    "false": "Open critical or security issues, or failing tests"
                }
            },
            "risk": {
                "type": "score",
                "instructions": "How risky is merging this pull request?",
                "criteria": ["None", "Low", "Moderate", "High", "Severe"]
            },
            "action": {
                "type": "choice",
                "instructions": "What should the pipeline do next?",
                "criteria": {
                    "merge": "Safe to merge now",
                    "fix": "Fixable issues; send findings to the fixer agent",
                    "human_review": "Ambiguous or high-stakes; needs a human",
                    "reject": "Fundamentally wrong approach; close the PR"
                }
            }
        }
    }
    
    try:
        response = requests.post(
            url,
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
            parsed = parse_jev_response(data)
            
            print("="*60)
            print("PARSED DECISION:")
            print("="*60)
            print(f"Merge Safe: {'YES' if parsed['merge_safe'] else 'NO'} (noul={parsed['noul']:.2f})")
            print(f"Risk: {parsed['risk_0_10']:.1f} / 10 (raw score={parsed['raw_score']:.2f})")
            print(f"Action: {parsed['action'].upper()}")
            print(f"Confidence: {parsed['confidence']:.1f}%")
            print(f"\nAction Probabilities:")
            for option, prob in parsed['probabilities'].items():
                print(f"  {option}: {prob:.1%}")
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
    # First test parser on real captures
    test_parser_on_real_captures()
    
    # Then test live API if key is available
    print("\n" + "="*60)
    print("TESTING LIVE JEV API")
    print("="*60)
    print()
    
    success = test_jev_api()
    sys.exit(0 if success else 1)
