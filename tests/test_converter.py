"""End-to-end tests for the v0.2.0 SMA-crossover converter (no LLM)."""

import pandas as pd
import pytest

from survival_alpha.converter import (
    ParseError,
    diff_trades,
    parse_sma_crossover,
    run_strategy,
    translate,
)


SIMPLE_PINE = """\
//@version=6
strategy("SMA Cross 50/200", overlay=true)

fastSma = ta.sma(close, 50)
slowSma = ta.sma(close, 200)

if ta.crossover(fastSma, slowSma)
    strategy.entry("Long", strategy.long)

if ta.crossunder(fastSma, slowSma)
    strategy.close("Long")
"""


def _make_step_data():
    """Build OHLC data that guarantees a clean SMA(50)/SMA(200) crossover.

    Layout (1200 bars):
      bars   0..400  -> price = 50  (both SMAs settle to 50)
      bars 401..800  -> price = 200 (sharp step up -> fast crosses above)
      bars 801..1199 -> price = 50  (sharp step down -> fast crosses below)
    """
    n = 1200
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    prices = ([50.0] * 401) + ([200.0] * 400) + ([50.0] * (n - 801))
    close = pd.Series(prices, index=idx, dtype=float)
    return pd.DataFrame(
        {"Open": close, "High": close, "Low": close, "Close": close},
        index=idx,
    )




# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class TestParser:
    def test_extracts_strategy_name(self):
        spec = parse_sma_crossover(SIMPLE_PINE)
        assert spec.strategy_name == "SMA Cross 50/200"

    def test_extracts_lengths(self):
        spec = parse_sma_crossover(SIMPLE_PINE)
        assert spec.fast_length == 50
        assert spec.slow_length == 200

    def test_extracts_var_names(self):
        spec = parse_sma_crossover(SIMPLE_PINE)
        assert spec.fast_var == "fastSma"
        assert spec.slow_var == "slowSma"

    def test_rejects_v5(self):
        bad = SIMPLE_PINE.replace("//@version=6", "//@version=5")
        with pytest.raises(ParseError, match="//@version=6"):
            parse_sma_crossover(bad)

    def test_rejects_rsi(self):
        bad = SIMPLE_PINE.replace(
            "slowSma = ta.sma(close, 200)",
            "slowSma = ta.sma(close, 200)\nrsi = ta.rsi(close, 14)",
        )
        with pytest.raises(ParseError, match="ta.rsi"):
            parse_sma_crossover(bad)

    def test_rejects_request_security(self):
        bad = SIMPLE_PINE + '\nhtf = request.security(syminfo.ticker, "1D", close)\n'
        with pytest.raises(ParseError, match="request.security"):
            parse_sma_crossover(bad)

    def test_rejects_strategy_short(self):
        bad = SIMPLE_PINE + '\nstrategy.short("S", strategy.short)\n'
        with pytest.raises(ParseError, match="strategy.short"):
            parse_sma_crossover(bad)

    def test_rejects_single_sma(self):
        bad = """//@version=6
strategy("only one")
sma1 = ta.sma(close, 50)
if close > sma1
    strategy.entry("L", strategy.long)
"""
        with pytest.raises(ParseError, match="2 .ta.sma"):
            parse_sma_crossover(bad)

    def test_rejects_indicator_script(self):
        bad = """//@version=6
indicator("foo")
plot(ta.sma(close, 50))
"""
        with pytest.raises(ParseError, match="strategy"):
            parse_sma_crossover(bad)

    def test_accepts_comments_and_blank_lines(self):
        # Comments and whitespace shouldn't break the parser.
        weird = """//@version=6
// my fancy SMA cross strategy
strategy("Comments OK")

// the fast one
fastSma = ta.sma(close, 50)
// and the slow one
slowSma = ta.sma(close, 200)



if ta.crossover(fastSma, slowSma)
    strategy.entry("Long", strategy.long)
if ta.crossunder(fastSma, slowSma)
    strategy.close("Long")
"""
        spec = parse_sma_crossover(weird)
        assert spec.fast_length == 50
        assert spec.slow_length == 200


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------

class TestTranslator:
    def test_emits_compilable_python(self):
        spec = parse_sma_crossover(SIMPLE_PINE)
        code = translate(spec)
        compile(code, "<generated>", "exec")  # raises SyntaxError if bad

    def test_emitted_code_runs_on_synthetic_data(self):
        spec = parse_sma_crossover(SIMPLE_PINE)
        code = translate(spec)
        ns = {}
        exec(code, ns)
        strategy_fn = ns["strategy"]

        data = _make_step_data()
        pos = strategy_fn(data)
        assert isinstance(pos, pd.Series)
        assert pos.index.equals(data.index)
        assert set(pos.unique()).issubset({0, 1})
        # By the end (after the down-step), strategy should be flat.
        assert pos.iloc[-1] == 0
        # Somewhere in the middle (during the up-step) it was long.
        assert pos.max() == 1


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class TestRunner:
    @pytest.fixture
    def strategy_fn(self):
        spec = parse_sma_crossover(SIMPLE_PINE)
        code = translate(spec)
        ns = {}
        exec(code, ns)
        return ns["strategy"]

    @pytest.fixture
    def trend_data(self):
        return _make_step_data()

    def test_produces_at_least_one_round_trip(self, strategy_fn, trend_data):
        trades = run_strategy(strategy_fn, trend_data)
        assert len(trades) >= 1

    def test_trades_have_expected_columns(self, strategy_fn, trend_data):
        trades = run_strategy(strategy_fn, trend_data)
        for col in ("entry_date", "exit_date", "entry_price", "exit_price",
                    "size_qty", "size_value", "pnl_usd", "pnl_pct"):
            assert col in trades.columns

    def test_trade_pnl_is_finite(self, strategy_fn, trend_data):
        # Whether the strategy MAKES money on this fixture is a property of
        # the strategy + data, not the pipeline. We only verify the math
        # produced a finite, non-NaN P&L number.
        trades = run_strategy(strategy_fn, trend_data)
        import math
        s = float(trades["pnl_usd"].sum())
        assert math.isfinite(s)

    def test_zero_commission_no_loss_on_breakeven(self, strategy_fn):
        # Constant price: no signals, no trades.
        n = 400
        idx = pd.date_range("2023-01-01", periods=n, freq="D")
        flat = pd.Series([100.0] * n, index=idx)
        data = pd.DataFrame(
            {"Open": flat, "High": flat, "Low": flat, "Close": flat}, index=idx
        )
        trades = run_strategy(strategy_fn, data)
        assert len(trades) == 0

    def test_commission_reduces_pnl(self, strategy_fn, trend_data):
        no_comm = run_strategy(strategy_fn, trend_data,
                               tv_config={"commission_pct": 0.0})
        with_comm = run_strategy(strategy_fn, trend_data,
                                 tv_config={"commission_pct": 0.5})
        assert with_comm["pnl_usd"].sum() < no_comm["pnl_usd"].sum()

    def test_rejects_non_series_return(self, trend_data):
        def bad_strategy(data):
            return [0] * len(data)  # not a Series
        with pytest.raises(TypeError, match="pd.Series"):
            run_strategy(bad_strategy, trend_data)

    def test_rejects_out_of_range_positions(self, trend_data):
        def naughty(data):
            return pd.Series([0] * (len(data) - 1) + [2], index=data.index)
        with pytest.raises(ValueError, match=r"\{0, 1\}"):
            run_strategy(naughty, trend_data)


# ---------------------------------------------------------------------------
# Differ
# ---------------------------------------------------------------------------

class TestDiffer:
    def test_perfect_match(self):
        df = pd.DataFrame({
            "entry_date": pd.to_datetime(["2023-01-01", "2023-06-01"]),
            "exit_date":  pd.to_datetime(["2023-03-01", "2023-08-01"]),
        })
        d = diff_trades(df, df.copy())
        assert d.is_perfect_match
        assert d.matched == 2
        assert d.match_pct == 100.0

    def test_partial_overlap(self):
        gen = pd.DataFrame({
            "entry_date": pd.to_datetime(["2023-01-01", "2023-06-01"]),
            "exit_date":  pd.to_datetime(["2023-03-01", "2023-08-01"]),
        })
        ref = pd.DataFrame({
            "entry_date": pd.to_datetime(["2023-01-01", "2023-07-01"]),
            "exit_date":  pd.to_datetime(["2023-03-01", "2023-09-01"]),
        })
        d = diff_trades(gen, ref)
        assert d.matched == 1
        assert len(d.gen_only) == 1
        assert len(d.ref_only) == 1
        assert not d.is_perfect_match

    def test_empty_both(self):
        empty = pd.DataFrame(columns=["entry_date", "exit_date"])
        d = diff_trades(empty, empty)
        assert d.matched == 0
        # Not "perfect" because there are no trades to match -- avoid false positives.
        assert not d.is_perfect_match


# ---------------------------------------------------------------------------
# End-to-end pipeline
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_pine_to_trades_pipeline(self):
        """Parse -> translate -> exec -> run -> get trades. Full vertical slice."""
        spec = parse_sma_crossover(SIMPLE_PINE)
        code = translate(spec)
        ns = {}
        exec(code, ns)

        data = _make_step_data()
        trades = run_strategy(ns["strategy"], data)
        assert len(trades) >= 1
        # Reconciliation: every trade has a matching exit -> non-NaN P&L
        assert trades["pnl_usd"].notna().all()
