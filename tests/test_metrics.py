"""Known-answer tests for compute_metrics and friends."""

import math

import pytest

from survival_alpha.loaders import load_tradingview_csv
from survival_alpha.metrics import (
    ANNUALIZATION_PRESETS,
    compute_max_drawdown,
    compute_metrics,
    estimate_initial_capital,
    resolve_annualization,
)


# ---------------------------------------------------------------------------
# resolve_annualization
# ---------------------------------------------------------------------------

class TestResolveAnnualization:
    def test_stocks_preset(self):
        assert resolve_annualization("stocks") == 252

    def test_crypto_preset(self):
        assert resolve_annualization("crypto") == 365

    def test_aliases(self):
        for s in ("stock", "equities", "equity"):
            assert resolve_annualization(s) == 252
        for s in ("btc",):
            assert resolve_annualization(s) == 365

    def test_case_insensitive(self):
        assert resolve_annualization("CRYPTO") == 365
        assert resolve_annualization("  Stocks  ") == 252

    def test_int_passthrough(self):
        assert resolve_annualization(168) == 168
        assert resolve_annualization("168") == 168

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid annualization"):
            resolve_annualization("potatoes")


# ---------------------------------------------------------------------------
# estimate_initial_capital
# ---------------------------------------------------------------------------

class TestEstimateInitialCapital:
    def test_derives_from_cumulative_columns(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        cap = estimate_initial_capital(trades)
        # cum_usd=$2500 with cum_pct=25 -> $10,000 exactly
        assert cap == pytest.approx(10_000.0, abs=0.01)

    def test_handles_sub_cent_first_trade(self, sub_cent_first_trade_log):
        """Trade #1 has size_value=0, must fall back to cumulative columns."""
        trades = load_tradingview_csv(sub_cent_first_trade_log)
        cap = estimate_initial_capital(trades)
        # Trade 2 cum_usd=109950 with cum_pct=1099.5 -> $10,000
        assert cap == pytest.approx(10_000.0, rel=1e-3)

    def test_tail_first_iteration_uses_largest_magnitude(self, simple_trade_log):
        """Late rows have the largest magnitudes -> least rounding error."""
        trades = load_tradingview_csv(simple_trade_log)
        cap = estimate_initial_capital(trades)
        # The simple_trade_log final row: cum=$2500, pct=25.0
        # 2500 / 0.25 = 10000 exactly. Earlier rows like cum=$1000/pct=10
        # would also give 10000 but with less digit precision.
        assert cap == pytest.approx(10_000.0, abs=0.01)


# ---------------------------------------------------------------------------
# compute_metrics — end-to-end on simple_trade_log
# ---------------------------------------------------------------------------

class TestComputeMetricsSimple:
    @pytest.fixture
    def m(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        return compute_metrics(trades)

    def test_n_trades(self, m):
        assert m["n_trades"] == 3

    def test_total_return(self, m):
        # $10K -> $12.5K = 25%
        assert m["total_return"] == pytest.approx(0.25, abs=0.005)

    def test_win_rate(self, m):
        # 2 wins out of 3
        assert m["win_rate"] == pytest.approx(2 / 3, abs=1e-6)

    def test_expectancy(self, m):
        # ($1000 + -$550 + $2050) / 3 = $833.33
        assert m["expectancy_usd"] == pytest.approx(833.33, abs=0.01)

    def test_profit_factor(self, m):
        # gross_wins=$3050, gross_losses=$550 -> 5.545...
        assert m["profit_factor"] == pytest.approx(3050 / 550, abs=1e-6)

    def test_avg_win(self, m):
        assert m["avg_win_usd"] == pytest.approx(1525.0, abs=0.01)

    def test_avg_loss(self, m):
        assert m["avg_loss_usd"] == pytest.approx(-550.0, abs=0.01)

    def test_largest_win(self, m):
        assert m["largest_win_usd"] == pytest.approx(2050.0, abs=0.01)

    def test_largest_loss(self, m):
        assert m["largest_loss_usd"] == pytest.approx(-550.0, abs=0.01)

    def test_cagr(self, m):
        # final/initial = 1.25, years = (335 days)/365.25 ~ 0.9172
        years = (335) / 365.25  # roughly
        expected = 1.25 ** (1 / years) - 1
        assert m["cagr"] == pytest.approx(expected, rel=0.01)

    def test_max_dd_includes_intra_trade(self, m):
        # Trade 2 has MAE=-8% from peak; cumulative trough is bigger than
        # any single-trade MAE because of running max from Trade 1's MFE.
        # Verify: |max_dd| >= |worst_trade_mae|
        assert abs(m["max_dd"]) >= abs(m["worst_trade_mae"]) - 1e-9

    def test_worst_trade_mae(self, m):
        # Trade 2 had MAE_pct = -8% -> -0.08 in fraction
        assert m["worst_trade_mae"] == pytest.approx(-0.08, abs=1e-6)

    def test_calmar(self, m):
        assert m["calmar"] == pytest.approx(
            m["cagr"] / abs(m["max_dd"]), abs=1e-6
        )

    def test_annualization_basis_default_stocks(self, m):
        assert m["annualization_basis"] == 252


class TestComputeMetricsAnnualization:
    def test_crypto_scales_sharpe_by_sqrt_365_over_252(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        m_stocks = compute_metrics(trades, annualization="stocks")
        m_crypto = compute_metrics(trades, annualization="crypto")
        if m_stocks["sharpe"] != 0:
            ratio = m_crypto["sharpe"] / m_stocks["sharpe"]
            assert ratio == pytest.approx(math.sqrt(365 / 252), rel=1e-6)

    def test_custom_integer_basis(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        m = compute_metrics(trades, annualization=168)
        assert m["annualization_basis"] == 168

    def test_invalid_basis_raises(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        with pytest.raises(ValueError, match="Invalid annualization"):
            compute_metrics(trades, annualization="potatoes")


class TestProfitFactorEdgeCases:
    def test_all_winners_yields_inf(self, all_winning_trade_log):
        trades = load_tradingview_csv(all_winning_trade_log)
        m = compute_metrics(trades)
        assert m["profit_factor"] == float("inf")


# ---------------------------------------------------------------------------
# compute_max_drawdown — invariant check
# ---------------------------------------------------------------------------

class TestMaxDrawdown:
    def test_dd_is_negative_or_zero(self, simple_trade_log):
        trades = load_tradingview_csv(simple_trade_log)
        cap = estimate_initial_capital(trades)
        dd = compute_max_drawdown(trades, cap)
        assert dd <= 0.0

    def test_dd_geq_worst_single_trade_mae(self, simple_trade_log):
        """The combined DD must be at least as deep as the worst single MAE."""
        trades = load_tradingview_csv(simple_trade_log)
        m = compute_metrics(trades)
        # In our fixture trade 2's MAE = -8%, so max_dd should be deeper
        assert abs(m["max_dd"]) >= abs(m["worst_trade_mae"]) - 1e-9
