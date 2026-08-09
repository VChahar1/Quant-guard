# Quant Safety Subsystem — Guard + Risk

**Author:** Vaibhav Chahar
**Status:** Working prototype, verified end-to-end (no API key needed to test)

---

## What this is

A safety layer for Quant's AI, in two modules under one subsystem:

- **Quant Guard** — checks every AI answer before it reaches the user, and
  catches: missing financial disclaimers, leaked private keys / emails, prompt
  injection, and **hallucinated numbers** (figures in the answer that don't
  match the real market data that was fetched). It then decides: allow, add a
  disclaimer, redact the risky part, or block.

- **Quant Risk** — scores the risk in a user's crypto portfolio (concentration,
  volatility, liquidity, rug/contract risk) and explains each score in plain
  language, to drive alerts and recommendations.

This maps onto two of the team's tasks: the User Protection Layer (#1) and
Portfolio Risk Scoring (#6).

## Why it's built the way it is

- **Cheap checks first, expensive ones only if needed** — fast regex runs before
  any model call, so it's low-latency and low-cost.
- **Shadow mode by default** — it can be dropped into a live system and will
  only *log* what it would do, changing nothing, until we're confident it isn't
  over-flagging. Flip one env var to turn on enforcement.
- **Prefer a disclaimer over a block** — over-blocking drives users away, so most
  issues get annotated, not withheld.
- **Everything is explainable** — every decision comes with the reasons behind
  it, which a financial product needs.

## See it work in 30 seconds (no API key, no setup)

From the folder that contains `quant_guard/`:

```bash
python3 quant_guard/selftest.py
```

Expected output: `PASSED 6/6 checks`. It runs the guard against sample answers —
a clean one (passes), advice with no disclaimer (annotated), a fabricated price
checked against real data (flagged), a leaked private key (redacted), an
injection attempt (blocked) — plus a real portfolio risk score.

No OpenAI/Anthropic key is needed for this. The AI model is only the thing that
*produces* text; the guard logic is independent and fully testable on its own.

## How it connects to a real system

`integration_vibe.py` is a ~90-line adapter that hooks the guard into the
open-source Vibe-Trading agent (used here as a realistic finance-AI test bed).
It attaches at the single point every AI response passes through. Only that one
file is app-specific — **porting to Quant means rewriting just that adapter** to
point at Quant's own response object and data sources; the whole guard/ and
risk/ core is unchanged.

We verified the full path live: with a funded API key, one real model call goes
through the guarded path and the guard logs its verdict on the model's actual
output. (Left the live API run aside for now; the self-test already proves the
logic.)

## What's real vs. what's next

**Working now:** the full guard pipeline, the concentration risk factor, the
policy engine, shadow mode, and the Vibe-Trading adapter — all tested.

**Needs data hookups (designed, stubbed honestly — they return "pending" rather
than fake numbers):** the market / liquidity / contract risk factors. These need
a market-data source. A crypto risk API like DD.xyz (Webacy) is a direct fit and
there's a grant on the table for it.

**Needs a model wire-up:** the "LLM-as-judge" checker for nuanced cases the
regex rules can't express.

## Files

```
quant_guard/
  selftest.py          <- run this first
  common/types.py      shared vocabulary (actions, findings, severities)
  guard/pipeline.py    the checker pipeline + policy engine
  guard/checkers.py    the individual checks
  risk/scoring.py      portfolio risk factors + composite score
  integration_vibe.py  adapter into the Vibe-Trading agent
```

See the accompanying design doc (`Quant_Safety_Subsystem_Design.docx`) for the
full architecture write-up.
