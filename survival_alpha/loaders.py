"""Loaders that normalize various trade-log formats into a canonical DataFrame."""

from pathlib import Path

import pandas as pd


def load_tradingview_csv(path):
    """Load a TradingView strategy tester trade log.

    TradingView exports two rows per trade (Entry + Exit, sharing the same
    Trade #). This function pairs them into one row per round-trip trade.

    Parameters
    ----------
    path : str or Path

    Returns
    -------
    pd.DataFrame
        One row per trade. Columns: trade_id, side, entry_date, exit_date,
        entry_signal, exit_signal, entry_price, exit_price, size_qty,
        size_value, pnl_usd, pnl_pct, mae_usd, mae_pct, mfe_usd, mfe_pct,
        cum_pnl_usd, cum_pnl_pct, duration_days.
    """
    path = Path(path)
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    required = {"Trade #", "Type", "Date and time", "Signal", "Price USD"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{path.name} doesn't look like a TradingView trade log "
            f"(missing columns: {sorted(missing)})."
        )

    entries = df[df["Type"].str.startswith("Entry", na=False)].copy()
    exits = df[df["Type"].str.startswith("Exit", na=False)].copy()

    if entries.empty or exits.empty:
        raise ValueError(f"{path.name} contains no paired entry/exit rows.")

    entries["side"] = (
        entries["Type"].str.replace("Entry ", "", regex=False).str.lower()
    )

    merged = entries.merge(exits, on="Trade #", suffixes=("_entry", "_exit"))

    out = pd.DataFrame(
        {
            "trade_id": merged["Trade #"].astype(int),
            "side": merged["side"],
            "entry_date": pd.to_datetime(merged["Date and time_entry"]),
            "exit_date": pd.to_datetime(merged["Date and time_exit"]),
            "entry_signal": merged["Signal_entry"],
            "exit_signal": merged["Signal_exit"],
            "entry_price": merged["Price USD_entry"].astype(float),
            "exit_price": merged["Price USD_exit"].astype(float),
            "size_qty": merged["Size (qty)_entry"].astype(float),
            "size_value": merged["Size (value)_entry"].astype(float),
            "pnl_usd": merged["Net P&L USD_entry"].astype(float),
            "pnl_pct": merged["Net P&L %_entry"].astype(float),
            "mae_usd": merged["Adverse excursion USD_entry"].astype(float),
            "mae_pct": merged["Adverse excursion %_entry"].astype(float),
            "mfe_usd": merged["Favorable excursion USD_entry"].astype(float),
            "mfe_pct": merged["Favorable excursion %_entry"].astype(float),
            "cum_pnl_usd": merged["Cumulative P&L USD_entry"].astype(float),
            "cum_pnl_pct": merged["Cumulative P&L %_entry"].astype(float),
        }
    )
    out["duration_days"] = (out["exit_date"] - out["entry_date"]).dt.days
    return out.sort_values("entry_date").reset_index(drop=True)
