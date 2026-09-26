"""
Tests for adapters
"""
import pytest
from src.models import Severity, Action
from src.adapters import (
    CannedCodeRabbitAdapter,
    StubJevAdapter,
    CannedLLMAdapter
)


def test_canned_coderabbit_first_review():
    """First review should have critical findings"""
    adapter = CannedCodeRabbitAdapter(inject_bug=True)
    findings = adapter.get_review(pr_number=1)
    
    assert len(findings) > 0
    critical_findings = [f for f in findings if f.severity == Severity.CRITICAL]
    assert len(critical_findings) > 0
    assert "authorization" in findings[0].message.lower()


def test_canned_coderabbit_second_review():
    """Second review should be clean after fix"""
    adapter = CannedCodeRabbitAdapter(inject_bug=True)
    
    # First review
    findings1 = adapter.get_review(pr_number=1)
    assert len(findings1) > 0
    
    # Second review (after fix)
    findings2 = adapter.get_review(pr_number=1)
    assert len(findings2) == 0


def test_stub_jev_blocks_on_critical():
    """Jev should block merge when critical findings exist"""
    adapter = StubJevAdapter()
    
    pr_state = {
        "findings": [
            {
                "severity": "critical",
                "message": "Security issue",
                "file": "app.py",
                "line": 10
            }
        ],
        "tests_pass": True,
        "attempt": 1
    }
    
    decision = adapter.decide(pr_state)
    
    assert decision.merge_safe is False
    assert decision.action == Action.FIX
    assert decision.risk > 5.0


def test_stub_jev_blocks_on_test_failure():
    """Jev should block merge when tests fail"""
    adapter = StubJevAdapter()
    
    pr_state = {
        "findings": [],
        "tests_pass": False,
        "attempt": 1
    }
    
    decision = adapter.decide(pr_state)
    
    assert decision.merge_safe is False
    assert decision.action == Action.FIX


def test_stub_jev_approves_clean_pr():
    """Jev should approve clean PR with passing tests"""
    adapter = StubJevAdapter()
    
    pr_state = {
        "findings": [],
        "tests_pass": True,
        "attempt": 1
    }
    
    decision = adapter.decide(pr_state)
    
    assert decision.merge_safe is True
    assert decision.action == Action.MERGE
    assert decision.risk < 2.0
    assert decision.confidence > 90.0


def test_stub_jev_human_review_on_max_attempts():
    """Jev should require human review after max attempts"""
    adapter = StubJevAdapter()
    
    pr_state = {
        "findings": [{"severity": "critical"}],
        "tests_pass": True,
        "attempt": 3  # Max attempts
    }
    
    decision = adapter.decide(pr_state)
    
    assert decision.action == Action.HUMAN_REVIEW


def test_canned_llm_generates_refund_code():
    """LLM should generate refund endpoint code"""
    adapter = CannedLLMAdapter()
    code = adapter.generate_code("Create a refund endpoint")
    
    assert "refund" in code.lower()
    assert "@app.post" in code or "def create_refund" in code
