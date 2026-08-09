from __future__ import annotations
import time
from typing import Protocol, runtime_checkable
from ..common.types import Action, Finding, RequestContext, Severity, Verdict

@runtime_checkable
class Checker(Protocol):
    name: str
    stage: str
    cost: str

    def check(self, text: str, ctx: RequestContext) -> list[Finding]:
        ...

class PolicyEngine:
    DEFAULT = {Severity.INFO: Action.ALLOW, Severity.LOW: Action.ANNOTATE, Severity.MEDIUM: Action.ANNOTATE, Severity.HIGH: Action.BLOCK, Severity.CRITICAL: Action.BLOCK}
    OVERRIDES = {'MISSING_DISCLAIMER': Action.ANNOTATE, 'PII_EMAIL': Action.REDACT, 'PII_WALLET_KEY': Action.REDACT, 'SELF_HARM': Action.ESCALATE, 'UNGROUNDED_CLAIM': Action.ANNOTATE}
    _RANK = {Action.ALLOW: 0, Action.ANNOTATE: 1, Action.REDACT: 2, Action.ESCALATE: 3, Action.BLOCK: 4}

    def resolve(self, findings: list[Finding]) -> Action:
        if not findings:
            return Action.ALLOW
        chosen = Action.ALLOW
        for f in findings:
            act = self.OVERRIDES.get(f.code, self.DEFAULT[f.severity])
            if self._RANK[act] > self._RANK[chosen]:
                chosen = act
        return chosen

class GuardPipeline:
    VERSION = 'guard-0.1.0'

    def __init__(self, checkers: list[Checker], policy: PolicyEngine | None=None):
        self.checkers = checkers
        self.policy = policy or PolicyEngine()

    def _ordered(self, stage: str) -> list[Checker]:
        stage_checks = [c for c in self.checkers if c.stage == stage]
        return sorted(stage_checks, key=lambda c: 0 if c.cost == 'cheap' else 1)

    def run(self, text: str, ctx: RequestContext, stage: str) -> Verdict:
        start = time.perf_counter()
        findings: list[Finding] = []
        for checker in self._ordered(stage):
            findings.extend(checker.check(text, ctx))
            if any((f.severity == Severity.CRITICAL for f in findings)):
                break
        action = self.policy.resolve(findings)
        return Verdict(action=action, findings=findings, latency_ms=(time.perf_counter() - start) * 1000, pipeline_version=self.VERSION)
