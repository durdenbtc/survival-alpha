"""Diff two trade lists by (entry_date, exit_date) keys.

A 'match' is a trade that appears in BOTH lists with the same entry
and exit dates. By default the match is strict (0-day tolerance); pass
``tolerance_days > 0`` to allow off-by-N-bar matches, which is useful
when comparing across data feeds (e.g. yfinance vs TradingView).
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
    fuzzy_matched: List[Tuple] = field(default_factory=list)
    tolerance_days: int = 0

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
            tol = (f" (\u00b1{self.tolerance_days}d)"
                   if self.tolerance_days else "")
            return f"[OK] {self.matched}/{self.matched} trades match{tol}."
        return (
            f"[WARN] Matched {self.matched} of "
            f"generated={self.total_generated} ref={self.total_reference}. "
            f"gen_only={len(self.gen_only)} ref_only={len(self.ref_only)}"
        )


def diff_trades(generated: pd.DataFrame, reference: pd.DataFrame,
                tolerance_days: int = 0) -> TradeDiff:
    """Compare two trade DataFrames by (entry_date, exit_date) tuples.

    Parameters
    ----------
    generated, reference : pd.DataFrame
        Must have 'entry_date' and 'exit_date' columns.
    tolerance_days : int, default 0
        If 0, requires exact-day match on both entry and exit.
        If > 0, a generated trade matches a reference trade when BOTH
        |entry_date_diff| <= tolerance_days AND |exit_date_diff| <= tolerance_days.

        Fuzzy matching uses greedy nearest-by-total-date-distance assignment:
        each generated trade matches AT MOST one reference trade, picked to
        minimize total day offset within tolerance.
    """
    def _pairs(df):
        if df.empty:
            return []
        ed = pd.to_datetime(df["entry_date"]).dt.date.tolist()
        xd = pd.to_datetime(df["exit_date"]).dt.date.tolist()
        return list(zip(ed, xd))

    g_pairs = _pairs(generated)
    r_pairs = _pairs(reference)

    if tolerance_days <= 0:
        g_set, r_set = set(g_pairs), set(r_pairs)
        matched = g_set & r_set
        return TradeDiff(
            matched=len(matched),
            total_generated=len(g_set),
            total_reference=len(r_set),
            gen_only=sorted(g_set - r_set),
            ref_only=sorted(r_set - g_set),
            tolerance_days=0,
        )

    # Fuzzy mode: greedy nearest-match.
    g_remaining = list(range(len(g_pairs)))
    r_remaining = list(range(len(r_pairs)))
    matched_count = 0
    fuzzy_pairs = []

    # Enumerate all candidate pairs within tolerance, sorted by total |delta|.
    candidates = []
    for gi, (g_e, g_x) in enumerate(g_pairs):
        for ri, (r_e, r_x) in enumerate(r_pairs):
            d_entry = abs((g_e - r_e).days)
            d_exit = abs((g_x - r_x).days)
            if d_entry <= tolerance_days and d_exit <= tolerance_days:
                candidates.append((d_entry + d_exit, gi, ri, g_pairs[gi], r_pairs[ri]))
    candidates.sort(key=lambda x: x[0])

    g_used, r_used = set(), set()
    for total_d, gi, ri, g_pair, r_pair in candidates:
        if gi in g_used or ri in r_used:
            continue
        g_used.add(gi)
        r_used.add(ri)
        matched_count += 1
        if total_d > 0:
            fuzzy_pairs.append((g_pair, r_pair, total_d))

    gen_only = sorted(g_pairs[i] for i in range(len(g_pairs)) if i not in g_used)
    ref_only = sorted(r_pairs[i] for i in range(len(r_pairs)) if i not in r_used)

    return TradeDiff(
        matched=matched_count,
        total_generated=len(g_pairs),
        total_reference=len(r_pairs),
        gen_only=gen_only,
        ref_only=ref_only,
        fuzzy_matched=fuzzy_pairs,
        tolerance_days=tolerance_days,
    )
