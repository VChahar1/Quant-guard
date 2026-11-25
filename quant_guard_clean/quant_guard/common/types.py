from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Action(str, Enum):
    ALLOW = "allow"
    ANNOTATE = "annotate"
    REDACT = "redact"
    BLOCK = "block"
    ESCALATE = "escalate"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Finding:
    code: str
    severity: Severity
    message: str
    span: Optional[tuple[int, int]] = None
    confidence: float = 1.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Verdict:
    action: Action
    findings: list[Finding] = field(default_factory=list)
    transformed_text: Optional[str] = None
    latency_ms: float = 0.0
    pipeline_version: str = ""

    @property
    def blocked(self) -> bool:
        return self.action in (Action.BLOCK, Action.ESCALATE)


@dataclass
class RequestContext:
    user_id: str
    session_id: str
    surface: str = "app"
    user_tier: str = "free"
    grounding_sources: list[str] = field(default_factory=list)
    locale: str = "en"
    meta: dict[str, Any] = field(default_factory=dict)
