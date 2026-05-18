"""Diff two trade lists by (entry_date, exit_date) keys.

A 'match' is a trade that appears in BOTH lists with the same entry
and exit dates. v0.2.0 uses exact-day matching; future versions may
allow ±N-bar tolerance.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

import pandas as pd


@dataclass
class TradeDiff:
    matched: int
    total_generated: int
    total_reference: int
    gen_only: List[Tuple] = field(default_factory=list)
    ref_only: List[Tuple] = field(default_factory=list)

    @property
    def match_pct(self) -> float:
        denom = max(self.total_generated, self.total_reference, 1)
        return 100.0 * self.matched / denom

    @property
    def is_perfect_match(self) -> bool:
        return (
            self.matched == self.total_generated
            and self.matched == self.total_reference
            and self.matched > 0
        )

    def summary(self) -> str:
        if self.is_perfect_match:
            return f"[OK] {self.matched}/{self.matched} trades match exactly."
        return (
            f"[WARN] Matched {self.matched} of "
            f"generated={self.total_generated} ref={self.total_reference}. "
            f"gen_only={len(self.gen_only)} ref_only={len(self.ref_only)}"
        )


def diff_trades(generated: pd.DataFrame, reference: pd.DataFrame) -> TradeDiff:
    """Compare two trade DataFrames by (entry_date, exit_date) tuples.

    Both must have 'entry_date' and 'exit_date' columns convertible to datetime.
    """
    def _keys(df):
        if df.empty:
            return set()
        ed = pd.to_datetime(df["entry_date"]).dt.date
        xd = pd.to_datetime(df["exit_date"]).dt.date
        return set(zip(ed, xd))

    g = _keys(generated)
    r = _keys(reference)
    matched = g & r
    return TradeDiff(
        matched=len(matched),
        total_generated=len(g),
        total_reference=len(r),
        gen_only=sorted(g - r),
        ref_only=sorted(r - g),
    )
