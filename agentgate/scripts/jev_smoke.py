#!/usr/bin/env python3
"""
Jev API smoke test - verifies JEV_API_KEY is valid
"""
import os
import sys
import requests
import json


def test_jev_api():
    """Test Jev API with a simple request"""
    api_key = os.getenv("JEV_API_KEY") or os.getenv("TYPESAFE_API_KEY")
    
    if not api_key:
        print("❌ JEV_API_KEY not set")
        print("\nSet either:")
        print("  export JEV_API_KEY=jv_live_...")
        print("  export TYPESAFE_API_KEY=jv_live_...")
        return False
    
    print(f"🔑 Found API key: {api_key[:15]}...")
    print("\n📡 Testing Jev API...")
    
    # Simple test request
    payload = {
        "model": "jev-latest",
        "state": "This is a test request to verify API authentication.",
        "questions": {
            "test": {
                "type": "noul",
                "question": "Is this a test?"
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
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Success! Jev API is working")
            print("\nResponse:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return False


if __name__ == "__main__":
    success = test_jev_api()
    sys.exit(0 if success else 1)
