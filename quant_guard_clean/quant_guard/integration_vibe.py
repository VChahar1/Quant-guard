from __future__ import annotations
import logging
import os
from typing import Any
from src.quant_guard.common.types import Action, RequestContext
from src.quant_guard.guard.pipeline import GuardPipeline
from src.quant_guard.guard.checkers import DisclaimerChecker, PIIChecker, GroundingChecker
log = logging.getLogger('quant_guard')
_PIPELINE = GuardPipeline([DisclaimerChecker(), PIIChecker(), GroundingChecker()])
_ENFORCE = os.getenv('QUANT_GUARD_ENFORCE', '0') == '1'
_DISCLAIMER = '\n\n---\n*Not financial advice. For informational purposes only; verify before acting.*'
_BLOCKED_MSG = "I can't share that response as written. Please rephrase, or ask for the underlying data and I'll walk you through it."

def _extract_grounding(messages: list[dict[str, Any]]) -> list[str]:
    sources: list[str] = []
    for m in messages or []:
        if m.get('role') in ('tool', 'function'):
            c = m.get('content')
            if isinstance(c, str):
                sources.append(c)
    return sources

def guard_llm_response(response, messages: list[dict[str, Any]] | None=None):
    text = getattr(response, 'content', None)
    if not text:
        return response
    ctx = RequestContext(user_id='vibe-local', session_id='vibe-session', surface='app', grounding_sources=_extract_grounding(messages or []))
    verdict = _PIPELINE.run(text, ctx, stage='output')
    if verdict.action != Action.ALLOW:
        log.info('quant_guard verdict=%s findings=%s latency_ms=%.2f', verdict.action.value, [f.code for f in verdict.findings], verdict.latency_ms)
    if not _ENFORCE:
        return response
    if verdict.action in (Action.BLOCK, Action.ESCALATE):
        response.content = _BLOCKED_MSG
    elif verdict.action == Action.ANNOTATE:
        if 'not financial advice' not in text.lower():
            response.content = text + _DISCLAIMER
    elif verdict.action == Action.REDACT:
        redacted = text
        for f in sorted(verdict.findings, key=lambda x: (x.span or (0, 0))[0], reverse=True):
            if f.span:
                s, e = f.span
                redacted = redacted[:s] + '[redacted]' + redacted[e:]
        response.content = redacted
    return response
