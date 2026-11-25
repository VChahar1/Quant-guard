"""Record actual scores for an explicitly synthetic portfolio."""

import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quant_guard_clean"))
from quant_guard.risk.scoring import (
    ConcentrationScorer,
    ContractScorer,
    LiquidityScorer,
    MarketScorer,
    Portfolio,
    PortfolioRiskModel,
    Position,
)


def main() -> None:
    """Show how placeholder factors dilute the prototype composite score."""
    root = Path(__file__).resolve().parents[1]
    portfolio = Portfolio(
        "fixture",
        [
            Position("A", "fixture", 1, 8000),
            Position("B", "fixture", 1, 1750),
            Position("C", "fixture", 1, 250),
        ],
    )
    result = PortfolioRiskModel(
        [ConcentrationScorer(), MarketScorer(), LiquidityScorer(), ContractScorer()]
    ).score(portfolio)
    payload = {
        "kind": "Synthetic portfolio; composite is not a validated risk measure",
        "position_values": [8000, 1750, 250],
        "composite": result.total,
        "factors": [
            {"factor": f.factor, "score": f.score, "meta": f.meta}
            for f in result.factors
        ],
    }
    (root / "results").mkdir(exist_ok=True)
    (root / "results/diagnostic.json").write_text(json.dumps(payload, indent=2) + "\n")
    labels = [f.factor for f in result.factors] + ["Composite"]
    values = [f.score for f in result.factors] + [result.total]
    fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
    bars = ax.bar(
        labels, values, color=["#176b60", "#9aa6b2", "#9aa6b2", "#9aa6b2", "#a7513b"]
    )
    ax.bar_label(bars, fmt="%.1f", padding=3)
    ax.set(
        ylabel="Prototype score",
        ylim=(0, 65),
        title="Synthetic portfolio · zero-valued stubs dilute the composite",
    )
    ax.spines[["top", "right"]].set_visible(False)
    (root / "assets").mkdir(exist_ok=True)
    fig.savefig(root / "assets/results.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
