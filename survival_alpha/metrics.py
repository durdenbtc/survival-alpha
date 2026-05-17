"""Performance metrics computed from a normalized trade DataFrame."""

import numpy as np
import pandas as pd


DEFAULT_ANNUALIZATION = 252       # stock convention (kept for backward compat)
CALENDAR_DAYS_PER_YEAR = 365.25

ANNUALIZATION_PRESETS = {
    "stocks": 252,
    "stock": 252,
    "equities": 252,
    "equity": 252,
    "crypto": 365,
    "btc": 365,
    "fx": 252,
    "forex": 252,
    "futures": 252,
}


def resolve_annualization(val):
    """Resolve a user-supplied annualization arg to an int trading-days-per-year.

    Accepts:
      - preset strings like 'stocks', 'crypto'
      - integer-like strings ('252', '365')
      - already-int values
    """
    if isinstance(val, int):
        return val
    s = str(val).lower().strip()
    if s in ANNUALIZATION_PRESETS:
        return ANNUALIZATION_PRESETS[s]
    try:
        return int(s)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid annualization '{val}'. Use a preset "
            f"({sorted(set(ANNUALIZATION_PRESETS.values()))}) or an integer."
        )


def estimate_initial_capital(trades):
    """Back out starting capital from TradingView's cumulative columns.

    TradingView guarantees: cum_pnl_usd / (cum_pnl_pct / 100) == initial_capital
    for every row that has both columns populated. This is more reliable than
    the first trade's `size_value`, which TradingView rounds to 0 when the
    entry price is sub-cent (e.g. BTC in 2010, micro-caps).

    Fallbacks: first non-zero size_value -> TradingView default of 10000.
    """
    # Walk from the LATEST trade backwards. Later rows have huge cumulative
    # magnitudes, so rounding in cum_usd / cum_pct is negligible. Early rows
    # can have small magnitudes where TV's 2-decimal rounding introduces
    # noticeable error in the implied capital.
    for _, row in trades.iloc[::-1].iterrows():
        cum_usd = row.get("cum_pnl_usd")
        cum_pct = row.get("cum_pnl_pct")
        if pd.notna(cum_usd) and pd.notna(cum_pct) and cum_pct != 0:
            cap = float(cum_usd) / (float(cum_pct) / 100.0)
            if cap > 0:
                return cap
    # Fallback: first non-zero size_value
    for _, row in trades.iterrows():
        sv = row.get("size_value")
        if pd.notna(sv) and float(sv) > 0:
            return float(sv)
    return 10_000.0  # TradingView default


def build_daily_equity_curve(trades):
    """Build a daily equity curve by distributing each trade's P&L
    pro-rata across the days it was open.

    Returns a Series of equity values (normalized so equity at start = 1.0).

    Notes
    -----
    Approximation that lets us derive daily-frequency Sharpe/Sortino from a
    trade log alone. For higher fidelity, Mode 2 (signal + price series)
    supplies mark-to-market daily values.
    """
    if trades.empty:
        return pd.Series(dtype=float)
    start = trades["entry_date"].min().normalize()
    end = trades["exit_date"].max().normalize()
    dates = pd.date_range(start, end, freq="D")
    initial_capital = estimate_initial_capital(trades)
    daily_pnl = pd.Series(0.0, index=dates)
    for _, t in trades.iterrows():
        d0 = t["entry_date"].normalize()
        d1 = t["exit_date"].normalize()
        n_days = max((d1 - d0).days, 1)
        pnl = float(t["pnl_usd"]) if pd.notna(t["pnl_usd"]) else 0.0
        per_day = pnl / n_days
        window = pd.date_range(d0 + pd.Timedelta(days=1), d1, freq="D")
        overlap = daily_pnl.index.intersection(window)
        daily_pnl.loc[overlap] += per_day
    equity = (initial_capital + daily_pnl.cumsum()) / initial_capital
    return equity


def _sharpe(daily_returns, days_per_year):
    s = daily_returns.std()
    if not s or s <= 0:
        return 0.0
    return float(daily_returns.mean() / s * np.sqrt(days_per_year))


def compute_max_drawdown(trades, initial_capital):
    """Max drawdown that includes intra-trade troughs.

    For each trade we emit four synthetic equity events in chronological
    order: entry, intra-trade extreme #1, intra-trade extreme #2, exit.
    The ordering of the two extremes is inferred from the trade's outcome:

      - Winning trades (pnl > 0) typically dip first, then recover.
        Order: trough (entry + MAE) -> peak (entry + MFE)
      - Losing trades (pnl <= 0) typically rally first, then collapse.
        Order: peak (entry + MFE) -> trough (entry + MAE)

    This is a heuristic, not a guarantee, but it produces a realistic
    estimate without creating phantom peaks that future trades would
    measure drawdown from. It always satisfies
    |max_dd| >= max single-trade |MAE_pct|.
    """
    if trades.empty:
        return 0.0
    ordered = trades.sort_values("entry_date").reset_index(drop=True)
    events = []
    running_pnl = 0.0
    for _, t in ordered.iterrows():
        entry_eq = initial_capital + running_pnl
        mfe = float(t["mfe_usd"]) if pd.notna(t.get("mfe_usd")) else 0.0
        mae = float(t["mae_usd"]) if pd.notna(t.get("mae_usd")) else 0.0
        pnl = float(t["pnl_usd"]) if pd.notna(t.get("pnl_usd")) else 0.0
        events.append(entry_eq)
        if pnl > 0:
            events.append(entry_eq + mae)
            events.append(entry_eq + mfe)
        else:
            events.append(entry_eq + mfe)
            events.append(entry_eq + mae)
        events.append(entry_eq + pnl)
        running_pnl += pnl
    s = pd.Series(events, dtype=float)
    running_max = s.cummax()
    dd = s / running_max - 1.0
    return float(dd.min())


def _sortino(daily_returns, days_per_year):
    """Standard Sortino: mean / downside_deviation * sqrt(days_per_year).

    Downside deviation = sqrt(mean(min(0, r)^2)) -- zero-padded for
    positive returns. Textbook formula (Sortino & Price 1994).
    """
    if len(daily_returns) == 0:
        return 0.0
    downside = np.minimum(daily_returns.values, 0.0)
    ddev = float(np.sqrt(np.mean(downside ** 2)))
    if ddev <= 0:
        return 0.0
    return float(daily_returns.mean() / ddev * np.sqrt(days_per_year))


def compute_metrics(trades, annualization="stocks"):
    """Return a dict of headline metrics for a trade DataFrame.

    Parameters
    ----------
    trades : pd.DataFrame
        Normalized trade list (see loaders.load_tradingview_csv).
    annualization : str or int, default "stocks"
        Trading days per year used to annualize Sharpe, Sortino, and Annual
        volatility. Presets: "stocks" (252), "crypto" (365). Integer also OK.
    """
    days_per_year = resolve_annualization(annualization)
    equity = build_daily_equity_curve(trades)
    daily_returns = equity.pct_change().dropna()
    start_date = trades["entry_date"].min()
    end_date = trades["exit_date"].max()
    years = max((end_date - start_date).days / CALENDAR_DAYS_PER_YEAR, 1e-9)
    final_equity = float(equity.iloc[-1]) if len(equity) else 1.0
    total_return = final_equity - 1.0
    cagr = final_equity ** (1 / years) - 1 if final_equity > 0 else -1.0
    sharpe = _sharpe(daily_returns, days_per_year)
    sortino = _sortino(daily_returns, days_per_year)
    annual_vol = float(daily_returns.std() * np.sqrt(days_per_year)) if len(daily_returns) else 0.0
    initial_cap = estimate_initial_capital(trades)
    max_dd = compute_max_drawdown(trades, initial_cap)
    calmar = cagr / abs(max_dd) if max_dd < 0 else 0.0
    total_days_in_market = float(trades["duration_days"].clip(lower=0).sum())
    total_calendar_days = max((end_date - start_date).days, 1)
    tim = min(total_days_in_market / total_calendar_days, 1.0)
    n_trades = len(trades)
    wins = trades[trades["pnl_usd"] > 0]
    losses = trades[trades["pnl_usd"] <= 0]
    win_rate = len(wins) / n_trades if n_trades else 0.0
    avg_win = float(wins["pnl_usd"].mean()) if len(wins) else 0.0
    avg_loss = float(losses["pnl_usd"].mean()) if len(losses) else 0.0
    largest_win = float(trades["pnl_usd"].max()) if n_trades else 0.0
    largest_loss = float(trades["pnl_usd"].min()) if n_trades else 0.0
    avg_duration = float(trades["duration_days"].mean()) if n_trades else 0.0
    expectancy = float(trades["pnl_usd"].mean()) if n_trades else 0.0
    gross_wins = float(wins["pnl_usd"].sum())
    gross_losses = float(abs(losses["pnl_usd"].sum()))
    profit_factor = gross_wins / gross_losses if gross_losses > 0 else float("inf")
    worst_trade_mae = float(trades["mae_pct"].min()) / 100 if n_trades else 0.0
    return {
        "start_date": start_date, "end_date": end_date, "years": years,
        "initial_equity": 1.0, "final_equity": final_equity,
        "total_return": total_return, "cagr": cagr,
        "sharpe": sharpe, "sortino": sortino, "calmar": float(calmar), "annual_vol": annual_vol,
        "max_dd": max_dd, "worst_trade_mae": worst_trade_mae,
        "annualization_basis": days_per_year,
        "time_in_market": tim, "n_trades": n_trades, "win_rate": win_rate,
        "expectancy_usd": expectancy, "profit_factor": profit_factor,
        "avg_win_usd": avg_win, "avg_loss_usd": avg_loss,
        "largest_win_usd": largest_win, "largest_loss_usd": largest_loss,
        "avg_duration_days": avg_duration,
    }
