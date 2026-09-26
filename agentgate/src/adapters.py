"""
Adapters for external services (GitHub, CodeRabbit, Jev, LLM)
Each adapter has offline/hybrid/live modes based on env vars.
"""
import os
import json
import time
import subprocess
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import requests

from .models import Finding, JevDecision, Action, Severity


class GitHubAdapter(ABC):
    """Abstract GitHub interface"""
    
    @abstractmethod
    def create_pr(self, branch: str, title: str, body: str) -> int:
        """Create a PR and return PR number"""
        pass
    
    @abstractmethod
    def get_pr_diff(self, pr_number: int) -> str:
        """Get PR diff"""
        pass
    
    @abstractmethod
    def merge_pr(self, pr_number: int):
        """Merge the PR"""
        pass
    
    @abstractmethod
    def add_comment(self, pr_number: int, comment: str):
        """Add a comment to PR"""
        pass


class LocalGitHubAdapter(GitHubAdapter):
    """Offline mode: uses local git"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
    
    def create_pr(self, branch: str, title: str, body: str) -> int:
        """Simulate PR creation"""
        # Just return a fake PR number
        return hash(branch) % 1000
    
    def get_pr_diff(self, pr_number: int) -> str:
        """Get diff from local git"""
        result = subprocess.run(
            ["git", "diff", "main...HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        return result.stdout
    
    def merge_pr(self, pr_number: int):
        """Simulate merge"""
        print(f"[LocalGitHub] Simulated merge of PR #{pr_number}")
    
    def add_comment(self, pr_number: int, comment: str):
        """Simulate comment"""
        print(f"[LocalGitHub] Simulated comment on PR #{pr_number}: {comment[:50]}...")


class LiveGitHubAdapter(GitHubAdapter):
    """Live mode: real GitHub API"""
    
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo  # owner/name
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
    
    def create_pr(self, branch: str, title: str, body: str) -> int:
        """Create real PR via GitHub API"""
        url = f"{self.base_url}/repos/{self.repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": branch,
            "base": "main"
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()["number"]
    
    def get_pr_diff(self, pr_number: int) -> str:
        """Get PR diff"""
        url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    
    def merge_pr(self, pr_number: int):
        """Merge PR"""
        url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/merge"
        response = requests.put(url, headers=self.headers)
        response.raise_for_status()
    
    def add_comment(self, pr_number: int, comment: str):
        """Add comment to PR"""
        url = f"{self.base_url}/repos/{self.repo}/issues/{pr_number}/comments"
        response = requests.post(url, headers=self.headers, json={"body": comment})
        response.raise_for_status()


class CodeRabbitAdapter(ABC):
    """Abstract CodeRabbit interface"""
    
    @abstractmethod
    def get_review(self, pr_number: int) -> List[Finding]:
        """Get normalized review findings"""
        pass
    
    @abstractmethod
    def request_review(self, pr_number: int):
        """Request a new review"""
        pass


class CannedCodeRabbitAdapter(CodeRabbitAdapter):
    """Offline mode: returns canned findings"""
    
    def __init__(self, inject_bug: bool = True):
        self.inject_bug = inject_bug
        self.review_count = 0
    
    def get_review(self, pr_number: int) -> List[Finding]:
        """Return canned findings"""
        self.review_count += 1
        
        # First review: always has a critical bug
        if self.review_count == 1 and self.inject_bug:
            return [
                Finding(
                    severity=Severity.CRITICAL,
                    category="security",
                    file="agentgate/demo-target/app.py",
                    line=75,
                    message="Missing authorization check: Any user can refund any payment. Verify that user_id from request matches the order's owner.",
                    suggested_fix="Add auth check: if orders_db[payment['order_id']]['user_id'] != refund.user_id: raise HTTPException(403)"
                ),
                Finding(
                    severity=Severity.MAINTAINABILITY,
                    category="code_quality",
                    file="agentgate/demo-target/app.py",
                    line=80,
                    message="Consider adding logging for refund operations for audit trail",
                    suggested_fix=None
                )
            ]
        
        # After fix: clean review
        return []
    
    def request_review(self, pr_number: int):
        """Simulate review request"""
        print(f"[CannedCodeRabbit] Simulated review request for PR #{pr_number}")


class LiveCodeRabbitAdapter(CodeRabbitAdapter):
    """Live mode: polls GitHub for CodeRabbit bot comments"""
    
    def __init__(self, github: GitHubAdapter, repo: str, token: str):
        self.github = github
        self.repo = repo
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
    
    def get_review(self, pr_number: int, timeout: int = 120) -> List[Finding]:
        """Poll for CodeRabbit review comments"""
        print(f"[LiveCodeRabbit] Polling for review on PR #{pr_number}...")
        
        start = time.time()
        while time.time() - start < timeout:
            findings = self._parse_comments(pr_number)
            if findings:
                return findings
            time.sleep(5)
        
        print("[LiveCodeRabbit] Timeout waiting for review")
        return []
    
    def _parse_comments(self, pr_number: int) -> List[Finding]:
        """Parse CodeRabbit comments into findings"""
        url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        findings = []
        for comment in response.json():
            # Look for coderabbitai[bot] comments
            if comment.get("user", {}).get("login") == "coderabbitai[bot]":
                finding = self._parse_comment(comment)
                if finding:
                    findings.append(finding)
        
        return findings
    
    def _parse_comment(self, comment: dict) -> Optional[Finding]:
        """Parse a single CodeRabbit comment"""
        body = comment.get("body", "")
        
        # Simple severity detection
        severity = Severity.SUGGESTION
        if any(word in body.lower() for word in ["critical", "security", "vulnerability"]):
            severity = Severity.CRITICAL
        elif "security" in body.lower():
            severity = Severity.SECURITY
        
        return Finding(
            severity=severity,
            category="review",
            file=comment.get("path", "unknown"),
            line=comment.get("line", 0),
            message=body[:200],  # Truncate for brevity
            suggested_fix=None
        )
    
    def request_review(self, pr_number: int):
        """Request CodeRabbit review by adding comment"""
        self.github.add_comment(pr_number, "@coderabbitai review")


class JevAdapter(ABC):
    """Abstract Jev decision interface"""
    
    @abstractmethod
    def decide(self, pr_state: Dict[str, Any]) -> JevDecision:
        """Make a decision on PR safety"""
        pass


class StubJevAdapter(JevAdapter):
    """Offline mode: deterministic decisions"""
    
    def decide(self, pr_state: Dict[str, Any]) -> JevDecision:
        """Deterministic decision logic"""
        findings = pr_state.get("findings", [])
        tests_pass = pr_state.get("tests_pass", True)
        attempt = pr_state.get("attempt", 1)
        
        # Always block on critical findings
        critical_count = sum(1 for f in findings if f["severity"] == "critical")
        
        if critical_count > 0 or not tests_pass:
            return JevDecision(
                merge_safe=False,
                confidence=95.0,
                risk=9.2,
                action=Action.FIX if attempt < 3 else Action.HUMAN_REVIEW
            )
        
        # Clean PR
        return JevDecision(
            merge_safe=True,
            confidence=98.0,
            risk=1.1,
            action=Action.MERGE
        )


class LiveJevAdapter(JevAdapter):
    """Live/Hybrid mode: real Jev API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.typesafe.ai/v1/systemone"
    
    def decide(self, pr_state: Dict[str, Any]) -> JevDecision:
        """Call real Jev API"""
        # Build state description
        findings = pr_state.get("findings", [])
        diff = pr_state.get("diff", "")
        tests_pass = pr_state.get("tests_pass", True)
        
        state = f"""PR Review Analysis:
- Files changed: {pr_state.get('files_changed', 0)}
- Findings: {len(findings)} ({sum(1 for f in findings if f.get('severity') == 'critical')} critical)
- Tests: {'passing' if tests_pass else 'failing'}
- Attempt: {pr_state.get('attempt', 1)}

Findings:
{json.dumps(findings, indent=2)}

Diff preview:
{diff[:500]}
"""
        
        # Build Jev request
        payload = {
            "model": "jev-latest",
            "state": state,
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
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse Jev response
            answers = data.get("answers", {})
            
            merge_safe_prob = answers.get("merge_safe", {}).get("noul", 0.5)
            risk_score = answers.get("risk", {}).get("score", 5.0)
            action_choice = answers.get("action", {}).get("choice", "human_review")
            
            return JevDecision(
                merge_safe=merge_safe_prob > 0.5,
                confidence=merge_safe_prob * 100,
                risk=risk_score,
                action=Action(action_choice),
                raw_response=data
            )
        
        except Exception as e:
            print(f"[Jev] API error: {e}, falling back to safe decision")
            # Fail safe: require human review
            return JevDecision(
                merge_safe=False,
                confidence=0.0,
                risk=10.0,
                action=Action.HUMAN_REVIEW,
                raw_response={"error": str(e)}
            )


class LLMAdapter(ABC):
    """Abstract LLM interface for code generation"""
    
    @abstractmethod
    def generate_code(self, prompt: str) -> str:
        """Generate code from prompt"""
        pass


class CannedLLMAdapter(LLMAdapter):
    """Offline mode: canned buggy and fixed code"""
    
    def __init__(self):
        self.call_count = 0
    
    def generate_code(self, prompt: str) -> str:
        """Return buggy implementation first, then fixed version"""
        self.call_count += 1
        
        if "refund" in prompt.lower() or "fix" in prompt.lower():
            # First call (builder): buggy code
            if self.call_count == 1:
                return '''

class Refund(BaseModel):
    payment_id: str
    amount: float
    user_id: str


@app.post("/refunds")
def create_refund(refund: Refund):
    """Create a refund for a payment"""
    if refund.payment_id not in payments_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payments_db[refund.payment_id]
    
    # BUG: Missing authorization check! Should verify user owns the order
    
    refund_id = str(uuid.uuid4())
    refund_data = {
        "id": refund_id,
        "payment_id": refund.payment_id,
        "amount": refund.amount,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    return refund_data
'''
            
            # Second call (fixer): fixed code
            else:
                # Return the COMPLETE fixed file
                return '''"""
Demo Target API - Orders and Payments Backend
This intentionally has bugs for the demo.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone

app = FastAPI(title="Demo Orders API")

# In-memory database
orders_db = {}
payments_db = {}
refunds_db = {}


class Order(BaseModel):
    id: Optional[str] = None
    user_id: str
    amount: float
    status: str = "pending"
    created_at: Optional[str] = None


class Payment(BaseModel):
    id: Optional[str] = None
    order_id: str
    amount: float
    status: str = "completed"
    created_at: Optional[str] = None


class Refund(BaseModel):
    payment_id: str
    amount: float
    user_id: str


@app.get("/")
def root():
    return {"message": "Orders API v1.0"}


@app.post("/orders")
def create_order(order: Order):
    order_id = str(uuid.uuid4())
    order.id = order_id
    order.created_at = datetime.now(timezone.utc).isoformat()
    orders_db[order_id] = order.dict()
    return orders_db[order_id]


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]


@app.post("/payments")
def create_payment(payment: Payment):
    if payment.order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[payment.order_id]
    if order["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot pay for cancelled order")
    
    payment_id = str(uuid.uuid4())
    payment.id = payment_id
    payment.created_at = datetime.now(timezone.utc).isoformat()
    payments_db[payment_id] = payment.dict()
    
    # Update order status
    orders_db[payment.order_id]["status"] = "paid"
    
    return payments_db[payment_id]


@app.get("/payments/{payment_id}")
def get_payment(payment_id: str):
    if payment_id not in payments_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payments_db[payment_id]


@app.post("/refunds")
def create_refund(refund: Refund):
    """Create a refund for a payment - FIXED VERSION"""
    if refund.payment_id not in payments_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payments_db[refund.payment_id]
    order_id = payment["order_id"]
    order = orders_db[order_id]
    
    # FIXED: Verify user owns the order
    if order["user_id"] != refund.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized: cannot refund other user's order")
    
    # FIXED: Validate refund amount
    if refund.amount > payment["amount"]:
        raise HTTPException(status_code=400, detail="Refund amount exceeds payment amount")
    
    # FIXED: Check for existing refund (prevent double refund)
    for existing_refund in refunds_db.values():
        if existing_refund["payment_id"] == refund.payment_id:
            raise HTTPException(status_code=400, detail="Payment already refunded")
    
    refund_id = str(uuid.uuid4())
    refund_data = {
        "id": refund_id,
        "payment_id": refund.payment_id,
        "amount": refund.amount,
        "user_id": refund.user_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    refunds_db[refund_id] = refund_data
    
    return refund_data
'''
        
        return "# Code generation not implemented"


class LiveLLMAdapter(LLMAdapter):
    """Live mode: real OpenAI/Anthropic"""
    
    def __init__(self, api_key: str, provider: str = "openai"):
        self.api_key = api_key
        self.provider = provider
    
    def generate_code(self, prompt: str) -> str:
        """Call real LLM API"""
        if self.provider == "openai":
            return self._call_openai(prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt)
        return "# LLM provider not supported"
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLM] OpenAI error: {e}")
            return f"# Error: {e}"
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]
        except Exception as e:
            print(f"[LLM] Anthropic error: {e}")
            return f"# Error: {e}"


def create_adapters(repo_path: str = "/workspace") -> Dict[str, Any]:
    """Factory to create adapters based on env vars"""
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "manvendersingh21/PR-slayer")
    jev_key = os.getenv("JEV_API_KEY") or os.getenv("TYPESAFE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Determine mode
    live_mode = bool(github_token)
    hybrid_mode = bool(jev_key and not github_token)
    
    # Create adapters
    if live_mode:
        github = LiveGitHubAdapter(github_token, github_repo)
        coderabbit = LiveCodeRabbitAdapter(github, github_repo, github_token)
    else:
        github = LocalGitHubAdapter(repo_path)
        coderabbit = CannedCodeRabbitAdapter()
    
    if jev_key:
        jev = LiveJevAdapter(jev_key)
    else:
        jev = StubJevAdapter()
    
    if openai_key:
        llm = LiveLLMAdapter(openai_key, "openai")
    elif anthropic_key:
        llm = LiveLLMAdapter(anthropic_key, "anthropic")
    else:
        llm = CannedLLMAdapter()
    
    mode = "live" if live_mode else ("hybrid" if hybrid_mode else "offline")
    
    return {
        "github": github,
        "coderabbit": coderabbit,
        "jev": jev,
        "llm": llm,
        "mode": mode
    }
