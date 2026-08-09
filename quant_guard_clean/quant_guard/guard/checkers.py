from __future__ import annotations
import re
from ..common.types import Finding, RequestContext, Severity

class DisclaimerChecker:
    name = 'disclaimer'
    stage = 'output'
    cost = 'cheap'
    _ADVICE_HINTS = re.compile('\\b(buy|sell|short|long|ape|should you|i recommend)\\b', re.I)
    _HAS_DISCLAIMER = re.compile('not (financial|investment) advice', re.I)

    def check(self, text: str, ctx: RequestContext) -> list[Finding]:
        if self._ADVICE_HINTS.search(text) and (not self._HAS_DISCLAIMER.search(text)):
            return [Finding(code='MISSING_DISCLAIMER', severity=Severity.LOW, message='Actionable financial language without a not-advice disclaimer.')]
        return []

class PIIChecker:
    name = 'pii'
    stage = 'output'
    cost = 'cheap'
    _EMAIL = re.compile('[\\w.+-]+@[\\w-]+\\.[\\w.-]+')
    _PRIVKEY = re.compile('\\b[0-9a-fA-F]{64}\\b')

    def check(self, text: str, ctx: RequestContext) -> list[Finding]:
        out: list[Finding] = []
        for m in self._EMAIL.finditer(text):
            out.append(Finding('PII_EMAIL', Severity.MEDIUM, 'Email address in output.', span=m.span()))
        for m in self._PRIVKEY.finditer(text):
            out.append(Finding('PII_WALLET_KEY', Severity.CRITICAL, 'Possible private key / seed material in output.', span=m.span()))
        return out

class PromptInjectionChecker:
    name = 'prompt_injection'
    stage = 'input'
    cost = 'cheap'
    _PATTERNS = re.compile('(ignore (all|previous) instructions|you are now|disregard the system|reveal your (system )?prompt)', re.I)

    def check(self, text: str, ctx: RequestContext) -> list[Finding]:
        if self._PATTERNS.search(text):
            return [Finding('PROMPT_INJECTION', Severity.HIGH, 'Input matches a known injection pattern.')]
        return []

class GroundingChecker:
    name = 'grounding'
    stage = 'output'
    cost = 'expensive'
    _NUMBER = re.compile('-?\\$?\\d[\\d,]*\\.?\\d*%?')

    def check(self, text: str, ctx: RequestContext) -> list[Finding]:
        if not ctx.grounding_sources:
            if not self._NUMBER.search(text):
                return []
            return [Finding('UNGROUNDED_CLAIM', Severity.LOW, 'Answer states figures but has no sources to verify against.', confidence=0.4)]
        source_blob = ' '.join(ctx.grounding_sources)
        findings: list[Finding] = []
        for m in self._NUMBER.finditer(text):
            token = m.group().lstrip('$').rstrip('%').replace(',', '')
            if token and token not in source_blob:
                findings.append(Finding('UNGROUNDED_CLAIM', Severity.MEDIUM, f"Figure '{m.group()}' not found in sources.", span=m.span(), confidence=0.6))
        return findings

class JudgeChecker:
    name = 'judge'
    stage = 'output'
    cost = 'expensive'

    def __init__(self, judge_fn=None):
        self._judge_fn = judge_fn

    def check(self, text: str, ctx: RequestContext) -> list[Finding]:
        if self._judge_fn is None:
            return []
        return self._judge_fn(text, ctx)
