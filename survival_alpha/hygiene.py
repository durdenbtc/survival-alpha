"""Lightweight hygiene checks for a TradingView trade log.

These are sanity checks. They do not replace real repaint detection or
look-ahead analysis, which require either the strategy source or daily
snapshot history (Mode 2 / Mode 3 in the roadmap).
"""

from dataclasses import dataclass


@dataclass
class Check:
    name: str
    status: str  # "pass" | "warn" | "fail"
    message: str


def check_negative_durations(trades):
    """Exits that occur before entries are corrupt data."""
    bad = trades[trades["duration_days"] < 0]
    if len(bad) == 0:
        return Check(
            "Trade durations",
            "pass",
            "All trades have non-negative duration.",
        )
    return Check(
        "Trade durations",
        "fail",
        f"{len(bad)} trade(s) exit before they entered — data is corrupt.",
    )


def check_same_bar_fills(trades):
    """Trades that enter and exit on the same bar can mask look-ahead bias."""
    same_bar = trades[trades["duration_days"] == 0]
    if len(same_bar) == 0:
        return Check(
            "Same-bar fills",
            "pass",
            "No trades enter and exit on the same bar.",
        )
    pct = len(same_bar) / len(trades) * 100
    status = "warn" if pct < 5 else "fail"
    return Check(
        "Same-bar fills",
        status,
        f"{len(same_bar)} of {len(trades)} trades ({pct:.1f}%) close on the same bar "
        "they opened. On daily data this can hide look-ahead bias.",
    )


def check_pnl_reconciliation(trades):
    """Sum of per-trade P&L should match the final cumulative P&L."""
    sum_pnl = float(trades["pnl_usd"].sum())
    final_cum = float(trades["cum_pnl_usd"].iloc[-1])
    diff = abs(sum_pnl - final_cum)
    rel = diff / abs(final_cum) if final_cum != 0 else 0.0
    if rel < 0.01:
        return Check(
            "P&L reconciliation",
            "pass",
            f"Per-trade P&L sums to ${sum_pnl:,.0f} vs cumulative ${final_cum:,.0f} "
            f"(Δ {rel*100:.3f}%).",
        )
    return Check(
        "P&L reconciliation",
        "warn",
        f"Per-trade sum (${sum_pnl:,.0f}) and cumulative (${final_cum:,.0f}) "
        f"differ by {rel*100:.2f}% — likely compounding interactions.",
    )


def check_sharpe_too_good(metrics):
    """Sharpe > 3 on daily data is suspicious for most retail strategies."""
    s = metrics["sharpe"]
    if s < 2.0:
        return Check(
            "Sharpe sanity",
            "pass",
            f"Sharpe of {s:.2f} is in a normal range for a daily strategy.",
        )
    if s < 3.0:
        return Check(
            "Sharpe sanity",
            "warn",
            f"Sharpe of {s:.2f} is high. Confirm costs, slippage, and out-of-sample "
            "testing have been applied.",
        )
    return Check(
        "Sharpe sanity",
        "fail",
        f"Sharpe of {s:.2f} is extremely high. Strong likelihood of look-ahead bias, "
        "overfit parameters, or unrealistic execution assumptions.",
    )


def check_profit_concentration(trades):
    """Top-N trades' share of total P&L. Heavy concentration means fragile alpha."""
    n = min(3, len(trades))
    total = float(trades["pnl_usd"].sum())
    if total <= 0:
        return Check(
            "Profit concentration",
            "warn",
            "Total P&L is non-positive — concentration check skipped.",
        )
    top_n = float(trades["pnl_usd"].nlargest(n).sum())
    pct = top_n / total * 100
    if pct < 40:
        return Check(
            "Profit concentration",
            "pass",
            f"Top {n} trades account for {pct:.1f}% of profit — well distributed.",
        )
    if pct < 70:
        return Check(
            "Profit concentration",
            "warn",
            f"Top {n} trades account for {pct:.1f}% of profit — strategy "
            "depends on a few outliers.",
        )
    return Check(
        "Profit concentration",
        "fail",
        f"Top {n} trades account for {pct:.1f}% of profit — remove these "
        "and the strategy likely fails.",
    )


def check_era_concentration(trades):
    """Does the strategy work across multiple calendar years?"""
    n_years = (
        trades["exit_date"].max() - trades["entry_date"].min()
    ).days / 365.25
    if n_years < 3:
        return Check(
            "Era concentration",
            "warn",
            f"Only {n_years:.1f} years of trade history — too short to validate "
            "across regimes.",
        )
    df = trades.copy()
    df["year"] = df["exit_date"].dt.year
    yearly = df.groupby("year")["pnl_pct"].sum()
    pos = int((yearly > 0).sum())
    total = int(len(yearly))
    pct = pos / total * 100 if total else 0
    if pct >= 70:
        return Check(
            "Era concentration",
            "pass",
            f"Profitable in {pos}/{total} calendar years ({pct:.0f}%).",
        )
    if pct >= 50:
        return Check(
            "Era concentration",
            "warn",
            f"Profitable in {pos}/{total} calendar years ({pct:.0f}%) — "
            "regime dependence is present.",
        )
    return Check(
        "Era concentration",
        "fail",
        f"Profitable in only {pos}/{total} calendar years ({pct:.0f}%) — "
        "high regime dependence.",
    )


def run_lightweight_checks(trades, metrics):
    """Run all v0.1 hygiene checks and return them as a list of Check objects."""
    return [
        check_negative_durations(trades),
        check_same_bar_fills(trades),
        check_pnl_reconciliation(trades),
        check_sharpe_too_good(metrics),
        check_profit_concentration(trades),
        check_era_concentration(trades),
    ]
