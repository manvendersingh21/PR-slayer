"""
Core data models for AgentGate
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    SUGGESTION = "suggestion"


class Action(str, Enum):
    MERGE = "merge"
    FIX = "fix"
    HUMAN_REVIEW = "human_review"
    REJECT = "reject"


@dataclass
class Finding:
    """CodeRabbit finding"""
    severity: Severity
    category: str
    file: str
    line: int
    message: str
    suggested_fix: Optional[str] = None


@dataclass
class JevDecision:
    """Jev decision output"""
    merge_safe: bool
    confidence: float  # 0-100%
    risk: float  # 0-10
    action: Action
    raw_response: dict = field(default_factory=dict)


@dataclass
class PRState:
    """Current state of a PR in the loop"""
    pr_number: int
    branch: str
    title: str
    findings: List[Finding] = field(default_factory=list)
    decision: Optional[JevDecision] = None
    attempt: int = 1
    max_attempts: int = 3
    test_results: dict = field(default_factory=dict)


@dataclass
class Event:
    """Event for dashboard streaming"""
    type: str  # builder_start, builder_complete, review_start, etc.
    pr_number: int
    data: dict = field(default_factory=dict)
    timestamp: Optional[str] = None
