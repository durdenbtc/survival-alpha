"""Loader smoke tests."""

import pandas as pd
import pytest

from survival_alpha.loaders import load_tradingview_csv


class TestLoadTradingViewCSV:
    def test_returns_one_row_per_trade(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        assert len(trades) == 3

    def test_has_canonical_columns(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        for col in ("trade_id", "side", "entry_date", "exit_date",
                    "pnl_usd", "pnl_pct", "mae_usd", "mfe_usd",
                    "cum_pnl_usd", "cum_pnl_pct", "duration_days"):
            assert col in trades.columns

    def test_sorted_by_entry_date(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        dates = trades["entry_date"].tolist()
        assert dates == sorted(dates)

    def test_empty_pnl_pct_becomes_nan_not_crash(self, sub_cent_first_trade_log):
        """Trade #1 in this fixture has empty Net P&L % — should be NaN, not crash."""
        trades = load_tradingview_csv(sub_cent_first_trade_log)
        assert len(trades) == 2
        # The first trade (2010-04-26) should have NaN pnl_pct
        first = trades.iloc[0]
        assert pd.isna(first["pnl_pct"])
        # But pnl_usd should be intact
        assert first["pnl_usd"] == 99950.0

    def test_missing_columns_raises_clear_error(self, tmp_path):
        bad = tmp_path / "bad.csv"
        bad.write_text("foo,bar\n1,2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="doesn't look like a TradingView trade log"):
            load_tradingview_csv(bad)
