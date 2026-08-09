from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

@dataclass
class Position:
    symbol: str
    chain: str
    qty: float
    usd_value: float
    contract_address: str | None = None

@dataclass
class Portfolio:
    user_id: str
    positions: list[Position]

    @property
    def total_usd(self) -> float:
        return sum((p.usd_value for p in self.positions)) or 1.0

@dataclass
class FactorResult:
    factor: str
    score: float
    explanation: str
    meta: dict = field(default_factory=dict)

@runtime_checkable
class FactorScorer(Protocol):
    factor: str

    def score(self, pf: Portfolio) -> FactorResult:
        ...

class ConcentrationScorer:
    factor = 'concentration'

    def score(self, pf: Portfolio) -> FactorResult:
        total = pf.total_usd
        weights = [p.usd_value / total for p in pf.positions]
        hhi = sum((w * w for w in weights))
        n = max(len(weights), 1)
        floor = 1.0 / n
        norm = 0.0 if hhi <= floor else (hhi - floor) / (1 - floor)
        top = max(weights) if weights else 0.0
        return FactorResult(self.factor, round(norm * 100, 1), explanation=f'Top holding is {top * 100:.0f}% of the book across {n} position(s).', meta={'hhi': round(hhi, 3)})

class MarketScorer:
    factor = 'market'

    def score(self, pf: Portfolio) -> FactorResult:
        return FactorResult(self.factor, 0.0, explanation='Market-risk scoring pending price feed.', meta={'status': 'stub'})

class LiquidityScorer:
    factor = 'liquidity'

    def score(self, pf: Portfolio) -> FactorResult:
        return FactorResult(self.factor, 0.0, explanation='Liquidity scoring pending depth data.', meta={'status': 'stub'})

class ContractScorer:
    factor = 'contract'

    def score(self, pf: Portfolio) -> FactorResult:
        unverified = [p.symbol for p in pf.positions if p.contract_address is None and p.chain != 'bitcoin']
        note = 'All positions carry contract metadata.' if not unverified else f'{len(unverified)} position(s) lack contract data: {', '.join(unverified[:5])}.'
        return FactorResult(self.factor, 0.0, explanation=note, meta={'status': 'stub', 'unverified': unverified})

@dataclass
class RiskScore:
    total: float
    band: str
    factors: list[FactorResult]

    def top_drivers(self, k: int=3) -> list[FactorResult]:
        return sorted(self.factors, key=lambda f: f.score, reverse=True)[:k]

class PortfolioRiskModel:
    DEFAULT_WEIGHTS = {'market': 0.3, 'concentration': 0.2, 'liquidity': 0.2, 'contract': 0.2, 'correlation': 0.1}

    def __init__(self, scorers: list[FactorScorer], weights: dict | None=None):
        self.scorers = scorers
        self.weights = weights or self.DEFAULT_WEIGHTS

    @staticmethod
    def _band(score: float) -> str:
        if score < 25:
            return 'low'
        if score < 50:
            return 'moderate'
        if score < 75:
            return 'elevated'
        return 'high'

    def score(self, pf: Portfolio) -> RiskScore:
        results = [s.score(pf) for s in self.scorers]
        num = sum((self.weights.get(r.factor, 0) * r.score for r in results))
        den = sum((self.weights.get(r.factor, 0) for r in results)) or 1.0
        total = round(num / den, 1)
        return RiskScore(total=total, band=self._band(total), factors=results)
