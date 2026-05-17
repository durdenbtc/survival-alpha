"""Test fixtures for survival-alpha.

Builds synthetic TradingView trade-log CSVs with hand-computable answers
so we can assert exact values from compute_metrics, etc.
"""

from pathlib import Path

import pandas as pd
import pytest


_TV_HEADER = (
    "Trade #,Type,Date and time,Signal,Price USD,Size (qty),Size (value),"
    "Net P&L USD,Net P&L %,Favorable excursion USD,Favorable excursion %,"
    "Adverse excursion USD,Adverse excursion %,Cumulative P&L USD,Cumulative P&L %"
)


def _row(*, trade_n, kind, date, signal, price, qty, size_val, pnl, pnl_pct,
         mfe, mfe_pct, mae, mae_pct, cum_usd, cum_pct):
    return ",".join(str(x) for x in [
        trade_n, kind, date, signal, price, qty, size_val,
        pnl, pnl_pct, mfe, mfe_pct, mae, mae_pct, cum_usd, cum_pct,
    ])


@pytest.fixture
def simple_trade_log(tmp_path):
    """Three round trips on $10,000 capital. Hand-computable answers:

      Trade 1 (long): enter 2024-01-15 @ $100, exit 2024-03-15 @ $110
                      qty=100 size_value=$10,000  pnl=+$1,000  pnl%=+10%
                      MFE=$1,500 (+15%)  MAE=-$200 (-2%)
      Trade 2 (long): enter 2024-04-15 @ $110, exit 2024-06-15 @ $104.50
                      qty=100 size_value=$11,000  pnl=-$550   pnl%=-5%
                      MFE=$220 (+2%)  MAE=-$880 (-8%)
      Trade 3 (long): enter 2024-07-15 @ $104.50, exit 2024-12-15 @ $125
                      qty=100 size_value=$10,450  pnl=+$2,050 pnl%=+19.62%
                      MFE=$2,700 (+25.84%)  MAE=-$300 (-2.87%)

    Cumulative P&L: $1,000 -> $450 -> $2,500
    Cumulative P&L %: 10% -> 4.5% -> 25%  (all against $10k initial)
    Final equity = $12,500 -> total return 25%
    Win rate: 2/3 = 66.67%
    Profit factor: $3,050 / $550 = 5.545454...
    Expectancy: $2,500 / 3 = $833.33
    Years: ~ (2024-12-15 - 2024-01-15).days / 365.25 = 335/365.25 = 0.9172
    CAGR: (1.25 ** (1/0.9172)) - 1 = ~27.66%

    Note: TV exports two rows per trade (Exit on top, then Entry below),
    same Trade # on both, P&L columns identical on both rows.
    """
    rows = [_TV_HEADER]

    def pair(*, n, entry_date, exit_date, entry_price, exit_price, qty,
             size_value, pnl, pnl_pct, mfe, mfe_pct, mae, mae_pct,
             cum_usd, cum_pct, signal="Long"):
        rows.append(_row(
            trade_n=n, kind="Exit long", date=exit_date,
            signal="Close position order",
            price=exit_price, qty=qty, size_val=size_value,
            pnl=pnl, pnl_pct=pnl_pct,
            mfe=mfe, mfe_pct=mfe_pct, mae=mae, mae_pct=mae_pct,
            cum_usd=cum_usd, cum_pct=cum_pct,
        ))
        rows.append(_row(
            trade_n=n, kind="Entry long", date=entry_date,
            signal=signal,
            price=entry_price, qty=qty, size_val=size_value,
            pnl=pnl, pnl_pct=pnl_pct,
            mfe=mfe, mfe_pct=mfe_pct, mae=mae, mae_pct=mae_pct,
            cum_usd=cum_usd, cum_pct=cum_pct,
        ))

    pair(n=1, entry_date="2024-01-15", exit_date="2024-03-15",
         entry_price=100, exit_price=110, qty=100, size_value=10000,
         pnl=1000, pnl_pct=10.0, mfe=1500, mfe_pct=15.0,
         mae=-200, mae_pct=-2.0, cum_usd=1000, cum_pct=10.0)
    pair(n=2, entry_date="2024-04-15", exit_date="2024-06-15",
         entry_price=110, exit_price=104.5, qty=100, size_value=11000,
         pnl=-550, pnl_pct=-5.0, mfe=220, mfe_pct=2.0,
         mae=-880, mae_pct=-8.0, cum_usd=450, cum_pct=4.5)
    pair(n=3, entry_date="2024-07-15", exit_date="2024-12-15",
         entry_price=104.5, exit_price=125, qty=100, size_value=10450,
         pnl=2050, pnl_pct=19.62, mfe=2700, mfe_pct=25.84,
         mae=-300, mae_pct=-2.87, cum_usd=2500, cum_pct=25.0)

    csv = tmp_path / "simple.csv"
    csv.write_text("\n".join(rows), encoding="utf-8")
    return csv


@pytest.fixture
def sub_cent_first_trade_log(tmp_path):
    """Trade #1 has size_value=0 (sub-cent price). Tests that
    estimate_initial_capital falls back to cumulative-column derivation."""
    rows = [_TV_HEADER]
    # Trade 1: BTC at $0.003 entry -> size_value rounds to 0
    rows.append(_row(
        trade_n=1, kind="Exit long", date="2010-09-06",
        signal="Close", price=0.06, qty=1666667, size_val=0,
        pnl=99950, pnl_pct="", mfe=150000, mfe_pct=0,
        mae=0, mae_pct=0, cum_usd=99950, cum_pct=999.50,
    ))
    rows.append(_row(
        trade_n=1, kind="Entry long", date="2010-04-26",
        signal="Long", price=0, qty=1666667, size_val=0,
        pnl=99950, pnl_pct="", mfe=150000, mfe_pct=0,
        mae=0, mae_pct=0, cum_usd=99950, cum_pct=999.50,
    ))
    # Trade 2: cleaner numbers
    rows.append(_row(
        trade_n=2, kind="Exit long", date="2011-01-01",
        signal="Close", price=1.0, qty=100000, size_val=109950,
        pnl=10000, pnl_pct=9.1, mfe=15000, mfe_pct=13.6,
        mae=-2000, mae_pct=-1.8, cum_usd=109950, cum_pct=1099.50,
    ))
    rows.append(_row(
        trade_n=2, kind="Entry long", date="2010-12-01",
        signal="Long", price=0.06, qty=100000, size_val=109950,
        pnl=10000, pnl_pct=9.1, mfe=15000, mfe_pct=13.6,
        mae=-2000, mae_pct=-1.8, cum_usd=109950, cum_pct=1099.50,
    ))
    csv = tmp_path / "subcent.csv"
    csv.write_text("\n".join(rows), encoding="utf-8")
    return csv


@pytest.fixture
def all_winning_trade_log(tmp_path):
    """No losing trades -> profit_factor should be inf, gross_losses=0."""
    rows = [_TV_HEADER]
    rows.append(_row(
        trade_n=1, kind="Exit long", date="2024-02-01",
        signal="Close", price=110, qty=100, size_val=10000,
        pnl=1000, pnl_pct=10.0, mfe=1500, mfe_pct=15.0,
        mae=-200, mae_pct=-2.0, cum_usd=1000, cum_pct=10.0,
    ))
    rows.append(_row(
        trade_n=1, kind="Entry long", date="2024-01-01",
        signal="Long", price=100, qty=100, size_val=10000,
        pnl=1000, pnl_pct=10.0, mfe=1500, mfe_pct=15.0,
        mae=-200, mae_pct=-2.0, cum_usd=1000, cum_pct=10.0,
    ))
    rows.append(_row(
        trade_n=2, kind="Exit long", date="2024-04-01",
        signal="Close", price=121, qty=100, size_val=11000,
        pnl=1100, pnl_pct=10.0, mfe=1500, mfe_pct=13.6,
        mae=-100, mae_pct=-0.9, cum_usd=2100, cum_pct=21.0,
    ))
    rows.append(_row(
        trade_n=2, kind="Entry long", date="2024-03-01",
        signal="Long", price=110, qty=100, size_val=11000,
        pnl=1100, pnl_pct=10.0, mfe=1500, mfe_pct=13.6,
        mae=-100, mae_pct=-0.9, cum_usd=2100, cum_pct=21.0,
    ))
    csv = tmp_path / "allwin.csv"
    csv.write_text("\n".join(rows), encoding="utf-8")
    return csv
