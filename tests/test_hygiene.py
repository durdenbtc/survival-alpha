"""Hygiene check tests, especially the era-concentration math (H4)."""

import pandas as pd

from survival_alpha.hygiene import (
    check_era_concentration,
    check_negative_durations,
    check_pnl_reconciliation,
    check_profit_concentration,
    check_same_bar_fills,
    check_sharpe_too_good,
)


def _make_trade(year, pnl_usd, pnl_pct, duration_days=30):
    return {
        "entry_date": pd.Timestamp(f"{year}-01-15"),
        "exit_date": pd.Timestamp(f"{year}-01-15") + pd.Timedelta(days=duration_days),
        "pnl_usd": pnl_usd,
        "pnl_pct": pnl_pct,
        "cum_pnl_usd": pnl_usd,  # not used in these checks for the smoke test
        "duration_days": duration_days,
    }


class TestEraConcentration:
    def test_pnl_usd_not_pnl_pct(self):
        """H4: era concentration must sum pnl_usd (dollar P&L), not pnl_pct."""
        # Year 1: net +$10,000 dollars, but sum of percentages negative
        # because we had one giant winner (5% on big size) and many small
        # losers (-3% each on tiny size). Summing pct gives wrong sign.
        df = pd.DataFrame([
            _make_trade(2020, +10_000, +5.0),
            _make_trade(2020, -100,    -3.0),
            _make_trade(2020, -100,    -3.0),
            _make_trade(2020, -100,    -3.0),
            _make_trade(2021, +5_000,  +20.0),
            _make_trade(2022, +5_000,  +20.0),
            _make_trade(2023, +5_000,  +20.0),
        ])
        check = check_era_concentration(df)
        # 2020 nets +$9,700 (positive), 2021/2022/2023 are positive.
        # All 4 years should be profitable -> 100% -> pass.
        # If we summed pnl_pct we'd get 2020 = 5 - 9 = -4 (negative)
        # and incorrectly count 3/4 = 75% (would still pass but wrong count).
        assert "Profitable in 4/4" in check.message
        assert check.status == "pass"

    def test_warns_when_history_too_short(self):
        df = pd.DataFrame([_make_trade(2024, +100, +1.0)])
        check = check_era_concentration(df)
        assert check.status == "warn"
        assert "too short" in check.message


class TestNegativeDurations:
    def test_pass_on_clean_data(self, simple_trade_log):
        from survival_alpha.loaders import load_tradingview_csv
        trades = load_tradingview_csv(simple_trade_log)
        c = check_negative_durations(trades)
        assert c.status == "pass"


class TestSharpeSanity:
    def test_normal_passes(self):
        c = check_sharpe_too_good({"sharpe": 1.2})
        assert c.status == "pass"

    def test_high_warns(self):
        c = check_sharpe_too_good({"sharpe": 2.5})
        assert c.status == "warn"

    def test_extreme_fails(self):
        c = check_sharpe_too_good({"sharpe": 6.5})
        assert c.status == "fail"


class TestPnlReconciliation:
    def test_clean_recon(self, simple_trade_log):
        from survival_alpha.loaders import load_tradingview_csv
        trades = load_tradingview_csv(simple_trade_log)
        c = check_pnl_reconciliation(trades)
        assert c.status == "pass"


class TestProfitConcentration:
    def test_three_equal_winners(self):
        df = pd.DataFrame([
            {"pnl_usd": 1000},
            {"pnl_usd": 1000},
            {"pnl_usd": 1000},
            {"pnl_usd": 1000},
            {"pnl_usd": 1000},
            {"pnl_usd": 1000},
            {"pnl_usd": 1000},
        ])
        c = check_profit_concentration(df)
        # top 3 / 7 = ~43% -> warn band (40-70)
        assert c.status == "warn"

    def test_one_big_winner_fails(self):
        df = pd.DataFrame([
            {"pnl_usd": 10_000},
            {"pnl_usd": 100},
            {"pnl_usd": 100},
            {"pnl_usd": 100},
        ])
        c = check_profit_concentration(df)
        assert c.status == "fail"
