"""Comparison module: symbol normalization, validation, and deterministic ranking."""
from __future__ import annotations

from core.models import CompareStockSummary

_ALLOWED_SYMBOL_CHARS = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-"
)


def normalize_compare_symbols(symbols: list[str]) -> list[str]:
    """Normalize and validate comparison symbols.

    - Strip whitespace
    - Uppercase symbols
    - Reject empty symbols
    - Reject duplicates after normalization
    - Enforce 2-4 unique symbols after normalization

    Returns the normalized list or raises ValueError with a clear message.
    """
    if not symbols:
        raise ValueError("At least 2 symbols are required (max 4).")

    normalized: list[str] = []
    seen: set[str] = set()

    for raw in symbols:
        s = raw.strip().upper() if raw else ""
        if not s:
            raise ValueError("Empty symbol after trimming is not allowed.")
        if (
            len(s) > 12
            or not s[0].isalpha()
            or any(ch not in _ALLOWED_SYMBOL_CHARS for ch in s)
        ):
            raise ValueError(
                "Symbols may contain only letters, numbers, dots, and hyphens, must start with a letter, and be 1-12 characters."
            )
        if s in seen:
            raise ValueError(f"Duplicate symbol detected after normalization: {s}")
        seen.add(s)
        normalized.append(s)

    if len(normalized) < 2:
        raise ValueError("At least 2 unique symbols are required.")
    if len(normalized) > 4:
        raise ValueError("At most 4 symbols are allowed.")

    return normalized


def _is_rankable(summary: CompareStockSummary) -> bool:
    """A summary is rankable only if it has meaningful analysis signals."""
    if summary.cio_action in ("BUY", "HOLD", "SELL"):
        return True
    if summary.confidence > 0:
        return True
    if summary.reliability_score > 0:
        return True
    if summary.grounding_score > 0:
        return True
    if summary.sentiment_score != 0.0:
        return True
    if summary.risk_level in ("Low", "Medium", "High"):
        return True
    if summary.valuation_verdict:
        return True
    if summary.top_bull_points or summary.top_bear_points or summary.key_risks:
        return True
    return False


def rank_comparison(summaries: list[CompareStockSummary]) -> tuple[str, str]:
    """Deterministic ranking: BUY > HOLD > SELL, then confidence, reliability, grounding, lower risk, sentiment.

    Only rankable summaries (those with meaningful signals) are considered.
    Returns (winner_symbol, ranking_rationale).  If no summaries are rankable,
    returns empty winner with a clear rationale.
    """
    rankable = [s for s in summaries if _is_rankable(s)]

    if not rankable:
        return "", "No valid completed summaries to rank."

    action_score = {"BUY": 3, "HOLD": 2, "SELL": 1, "": 0}
    risk_score_dict = {"Low": 3, "Medium": 2, "High": 1, "": 0}

    def score(s: CompareStockSummary) -> float:
        return round(
            action_score.get(s.cio_action, 0) * 3.0
            + s.confidence * 2.0
            + s.reliability_score * 1.5
            + s.grounding_score * 1.5
            + risk_score_dict.get(s.risk_level, 0) * 1.0
            + (s.sentiment_score + 1.0) * 1.0,  # shift -1..1 to 0..2
            4,
        )

    scored = [(score(s), s) for s in rankable]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return "", "No valid completed summaries to rank."

    winner = scored[0][1]
    rationale_parts = ["Ranking rationale (higher = stronger):"]
    for rank_score, s in scored:
        rationale_parts.append(
            f"  {s.symbol}: score={rank_score} (action={s.cio_action}, conf={s.confidence}, "
            f"reliab={s.reliability_score}, ground={s.grounding_score})"
        )

    # Also list non-rankable summaries
    non_rankable = [s for s in summaries if not _is_rankable(s)]
    if non_rankable:
        rationale_parts.append("")
        rationale_parts.append("Excluded from ranking (no valid analysis signals):")
        for s in non_rankable:
            rationale_parts.append(f"  {s.symbol}")

    return winner.symbol, "\n".join(rationale_parts)
