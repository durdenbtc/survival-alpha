"""Execute a strategy(data) function and produce a trade list.

Currently supports:
  - fill_mode = 'bar_close' (TradingView's most common default)
  - long-only positions (0 or 1)
  - constant pct-of-equity sizing
  - flat commission
"""

import pandas as pd


DEFAULT_TV_CONFIG = {
    "fill_mode": "bar_close",   # 'bar_close' | 'next_open' (v0.2.0: bar_close only)
    "initial_capital": 10_000.0,
    "order_size_pct": 99.0,     # % of current equity per entry
    "commission_pct": 0.0,      # % per side (entry + exit each charged)
}


_TRADE_COLUMNS = [
    "entry_date", "exit_date", "entry_price", "exit_price",
    "size_qty", "size_value", "pnl_usd", "pnl_pct",
]


def run_strategy(strategy_fn, data, tv_config=None):
    """Execute `strategy_fn(data)` and build a trade list.

    Returns a pd.DataFrame with one row per round-trip trade (matches the
    canonical shape of survival_alpha.loaders.load_tradingview_csv).
    """
    cfg = {**DEFAULT_TV_CONFIG, **(tv_config or {})}
    if cfg["fill_mode"] != "bar_close":
        raise NotImplementedError(
            f"fill_mode='{cfg['fill_mode']}' not supported in v0.2.0; "
            "use 'bar_close'."
        )
    if "Close" not in data.columns:
        raise ValueError("data must have a 'Close' column.")

    position = strategy_fn(data)
    if not isinstance(position, pd.Series):
        raise TypeError(f"strategy must return pd.Series, got {type(position).__name__}.")
    if not position.index.equals(data.index):
        raise ValueError("strategy return index must match data index.")
    if not position.isin({0, 1}).all():
        bad = sorted(set(position.unique()) - {0, 1})
        raise ValueError(f"position values must be in {{0, 1}}; saw {bad}.")

    prev_pos = position.shift(1).fillna(0).astype(int)

    trades = []
    open_trade = None
    capital = float(cfg["initial_capital"])
    order_pct = float(cfg["order_size_pct"]) / 100.0
    comm_pct = float(cfg["commission_pct"]) / 100.0

    for i in range(len(data)):
        curr = int(position.iloc[i])
        prv = int(prev_pos.iloc[i])
        date = data.index[i]
        price = float(data.iloc[i]["Close"])

        if prv == 0 and curr == 1:
            size_value = capital * order_pct
            qty = size_value / price
            open_trade = {
                "entry_date": date,
                "entry_price": price,
                "size_qty": qty,
                "size_value": size_value,
            }
        elif prv == 1 and curr == 0 and open_trade is not None:
            qty = open_trade["size_qty"]
            entry_value = open_trade["size_value"]
            gross_pnl = (price - open_trade["entry_price"]) * qty
            commission = entry_value * comm_pct + (price * qty) * comm_pct
            pnl_usd = gross_pnl - commission
            pnl_pct = (pnl_usd / entry_value) * 100.0

            trades.append({
                **open_trade,
                "exit_date": date,
                "exit_price": price,
                "pnl_usd": pnl_usd,
                "pnl_pct": pnl_pct,
            })
            capital += pnl_usd
            open_trade = None

    if not trades:
        return pd.DataFrame(columns=_TRADE_COLUMNS)
    return pd.DataFrame(trades)[_TRADE_COLUMNS]
