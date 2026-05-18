# survival-alpha — TODO

## ✅ Shipped in v0.2.0

- **Rule-based Pine → Python translator** for SMA crossover strategies
  - Pre-flight gate rejects unsupported constructs with clear errors
  - Template-based code generation (no LLM yet — coming in v0.2.2)
- **`sa convert` CLI subcommand** with auto-detection from `./convert/`
- **Strategy runner** that executes `def strategy(data) -> pd.Series` against OHLC data
- **Trade differ** with `--tolerance N` flag for off-by-N-day matching across data feeds
- **23 new tests** for the converter pipeline (parser, translator, runner, differ, end-to-end)
- Verified end-to-end: SA-TEST 01 SMA(14/28) Pine → Python → 80/80 trades, 93.8% match against TradingView's COINBASE:BTCUSD reference with ±1d tolerance

---

The audit punch list from before v0.1 was published, minus the items already
fixed. Pick anything from here and open a PR. Items are roughly ordered by
priority within each section.

---

## 🟡 Open robustness / correctness items

### M2 — CI on push / PR
No `.github/workflows/` yet. A simple action that runs `pip install -e ".[dev]" && pytest` on every push and PR is the obvious first step. Should also lint with `ruff` once the codebase grows.

### M4 — Entry/Exit merge can cartesian-explode on scale-ins
`loaders.load_tradingview_csv` does `entries.merge(exits, on="Trade #")`. If a strategy uses scale-ins (multiple Entries with the same Trade #) or partial exits (multiple Exits), pandas silently cartesian-products them — wrong P&L sums, wrong everything.

**Fix:** After splitting into entries and exits, validate `groupby("Trade #").size() == 1` on each side. Raise a clear error: *"Trade #N has M entries and K exits — scale-ins / partial-exits not yet supported in v0.1."*

### M5 — Version is in two places
`pyproject.toml` has `version = "0.1.0"` and `survival_alpha/__init__.py` has `__version__ = "0.1.0"`. They can drift. Use `dynamic = ["version"]` in pyproject and read from `__init__.py` via `[tool.setuptools.dynamic]`.

### M8 — Sharpe hygiene threshold is uncalibrated
The Sharpe sanity check fires at >2 (warn) and >3 (fail). Those thresholds assume the Sharpe is honest — but in Mode 1 we know it's structurally inflated by the pro-rata daily curve (~30-50% high vs true daily MTM). The thresholds should probably be raised, or the check should say *"...high; note this is the Mode-1 number which is inflated; consider Mode 2 before believing it."*

---

## 🟢 Low-priority polish

### L3 — Same-bar fills only flags duration == 0
Could also flag duration == 1 (next-bar fills) as a softer warning. Some "On bar close" TradingView strategies legitimately fill same-bar; some look-ahead bugs fill next-bar. Worth surfacing both.

### L4 — Currency assumed USD
All P&L fields are named `*_usd`. TradingView can export in any currency. For v0.1 it's documented as "USD only" by virtue of field names; a future version should accept `--currency EUR` or auto-detect from the CSV header.

### L5 — `tearsheet` subcommand is a near-duplicate of the group default
`sa` (group default) and `sa tearsheet` do the same thing. Click-idiomatic but redundant. Either drop the explicit subcommand or use it for something distinct (e.g. force a refresh, dump JSON, etc.).

### L7 — Date parsing assumes ISO daily format
`pd.to_datetime` handles ISO dates by default. Intraday TradingView exports (`2024-05-17 14:30`) parse, but timezone info is dropped if present. Document the assumption and consider accepting `--tz` for intraday logs.

### L8 — MFE_pct collected but never displayed
The loader pulls `mfe_pct` into the canonical DataFrame but no metric surfaces it. Either add a "Best trade MFE" line to the Performance panel (mirror of "Worst trade MAE") or drop the column from the loader.

### L6 — No CONTRIBUTING.md / CHANGELOG.md
Standard at v1.0. CHANGELOG starts mattering once anything other than 0.1.0 ships.

---

## ✨ Feature ideas (from the field)

### `--start-date` / `--end-date` filtering
Right now the metrics use the full trade history. For strategies with very long histories (e.g. Rule 6 starting in 2010 when BTC was sub-cent), this dwarfs more recent performance and makes comparison to strategies that start later impossible.

A `--start-date 2014-05-20` flag would filter the trade log before computing metrics, enabling apples-to-apples comparison across strategies with different start dates. Pair with `--end-date` for window-locked analysis.

### "Era mismatch detected" hygiene check
When a trade log starts before some early-BTC threshold (say 2014) AND total return is suspiciously huge (>1,000,000%) AND profit concentration is high, fire a warn: *"Your backtest captures the 2010-2014 BTC era where price moved ~167,000×. Inflated returns here are an era effect, not a strategy effect. Consider `--start-date 2014-01-01` for fair comparison."*

### Tearsheet export
`sa my-log.csv --export pdf` → render the rich panels to a single-page PDF. `--export json` → machine-readable for downstream tools. `--export png` → screenshot-able tearsheet for Substack posts.

### Equity-curve chart
Today `compute_metrics` builds an equity curve internally but doesn't surface it. A `--chart` flag (matplotlib) or `--chart-html` (plotly) would render the curve next to the tearsheet.

### Side-by-side strategy comparison
`sa compare a.csv b.csv` → renders both tearsheets in adjacent columns with delta highlights. Natural extension of the existing layout.

### Bring-your-own equity curve
For users who already have MTM equity data (e.g. exported from their broker), an `--equity-csv` flag would skip the pro-rata reconstruction and use the real curve for Sharpe/Sortino/Max DD. Effectively a Mode 1.5.

### Survival-Alpha Score (v1.0 brand mark)
The single headline metric that captures the *Survival Is Alpha* thesis. Likely something in the family of `geometric_return / max_drawdown × (1 − p_ruin)` but the exact formula needs design. Once defined, this becomes THE number people screenshot.

---

## 🔭 Out of v0.1 scope (parked for v0.2+)

These are deliberately not in v0.1. See `v0_2_PLAN.md` (gitignored, local) for the v0.2 architecture.

- **Pine Script → Python converter** (v0.2). LLM-assisted via Ollama + Qwen2.5-Coder-7B. Pre-flight gate, system prompt + few-shot pairs, static validators, trade-diff. The full plan is in `v0_2_PLAN.md`.
- **Mode 2** (v0.3): signal + price series → real MTM equity curve. Unlocks honest Sharpe/Sortino/vol, true repaint detection.
- **Mode 3** (v0.4): strategy-as-function. Lets users register a `def strategy(state) -> position` and run parameter sweeps with Pareto-frontier selection + sub-window forward tests.
- **Regime-conditional analysis** (v1.0): if MRE-style regime labels are provided, break down all metrics conditioned on regime state.

---

## 🐛 Known limitations of v0.1

Things v0.1 does NOT promise to do well. Flag these to users; don't pretend.

- **Sharpe / Sortino / Annual vol are structurally inflated** because the pro-rata daily equity curve smooths intra-trade volatility. We disclose this in the footer of every run. Mode 2 (v0.3) fixes it.
- **`compute_max_drawdown` uses a pnl-sign heuristic** to order intra-trade peak vs trough. This is a realistic default, not a guarantee. Edge cases: a winning trade that gapped down at the open and crawled back, or a losing trade that hit MFE on the final bar before stopping out — these will be slightly off.
- **TradingView's "Default order size: 99% of equity"** with full compounding produces astronomical dollar P&Ls over long histories (Rule 6 from 2010 ≈ $57B from $10K). Numbers are mathematically correct given the simulation but don't reflect what's executable in real markets at that scale. Worth a note in the docs.
- **Single-currency assumption (USD)** — see L4 above.

---

## 🎁 Marketing / community follow-ups

Not code, but worth tracking.

- **Substack launch post**: *"I built `survival-alpha` to catch the lies in my own backtests. Here's what it found in the 8th Rule."* The Era concentration finding (10/13 → 11/13 years after H4) is a natural anecdote.
- **Side-by-side post**: Run all your existing strategies through it, screenshot the tearsheets. Visual proof of the tool's reach.
- **PyPI publication**: requires building a wheel, registering the project name on PyPI, and pushing. Once published, the install becomes `pipx install survival-alpha`.
- **Repo description on GitHub**: *"Your backtest is lying to you. survival-alpha catches it. CLI for hygiene checks, real tearsheets, Pine→Python."*
