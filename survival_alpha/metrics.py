"""Performance metrics computed from a normalized trade DataFrame."""

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252
CALENDAR_DAYS_PER_YEAR = 365.25


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
    initial_capital = float(trades.iloc[0]["size_value"])
    daily_pnl = pd.Series(0.0, index=dates)
    for _, t in trades.iterrows():
        d0 = t["entry_date"].normalize()
        d1 = t["exit_date"].normalize()
        n_days = max((d1 - d0).days, 1)
        per_day = float(t["pnl_usd"]) / n_days
        window = pd.date_range(d0 + pd.Timedelta(days=1), d1, freq="D")
        overlap = daily_pnl.index.intersection(window)
        daily_pnl.loc[overlap] += per_day
    equity = (initial_capital + daily_pnl.cumsum()) / initial_capital
    return equity


def _sharpe(daily_returns):
    s = daily_returns.std()
    if not s or s <= 0:
        return 0.0
    return float(daily_returns.mean() / s * np.sqrt(TRADING_DAYS_PER_YEAR))


def _sortino(daily_returns):
    """Standard Sortino: mean / downside_deviation * sqrt(252).

    Downside deviation = sqrt(mean(min(0, r)^2)) -- zero-padded for
    positive returns. This is the textbook formula (e.g. Sortino & Price 1994).
    """
    if len(daily_returns) == 0:
        return 0.0
    downside = np.minimum(daily_returns.values, 0.0)
    ddev = float(np.sqrt(np.mean(downside ** 2)))
    if ddev <= 0:
        return 0.0
    return float(daily_returns.mean() / ddev * np.sqrt(TRADING_DAYS_PER_YEAR))


def compute_metrics(trades):
    """Return a dict of headline metrics for a trade DataFrame."""
    equity = build_daily_equity_curve(trades)
    daily_returns = equity.pct_change().dropna()
    start_date = trades["entry_date"].min()
    end_date = trades["exit_date"].max()
    years = max((end_date - start_date).days / CALENDAR_DAYS_PER_YEAR, 1e-9)
    final_equity = float(equity.iloc[-1]) if len(equity) else 1.0
    total_return = final_equity - 1.0
    cagr = final_equity ** (1 / years) - 1 if final_equity > 0 else -1.0
    sharpe = _sharpe(daily_returns)
    sortino = _sortino(daily_returns)
    annual_vol = float(daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(daily_returns) else 0.0
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_dd = float(drawdown.min()) if len(drawdown) else 0.0
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
    max_intra_trade_dd = float(trades["mae_pct"].min()) / 100 if n_trades else 0.0
    return {
        "start_date": start_date, "end_date": end_date, "years": years,
        "initial_equity": 1.0, "final_equity": final_equity,
        "total_return": total_return, "cagr": cagr,
        "sharpe": sharpe, "sortino": sortino, "calmar": float(calmar), "annual_vol": annual_vol,
        "max_dd": max_dd, "max_intra_trade_dd": max_intra_trade_dd,
        "time_in_market": tim, "n_trades": n_trades, "win_rate": win_rate,
        "expectancy_usd": expectancy, "profit_factor": profit_factor,
        "avg_win_usd": avg_win, "avg_loss_usd": avg_loss,
        "largest_win_usd": largest_win, "largest_loss_usd": largest_loss,
        "avg_duration_days": avg_duration, "equity_curve": equity,
    }
