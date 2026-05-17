# `survival-alpha` — High-Level Plan

> Status: planning. No code yet.

## Positioning

**One-liner:** *Your backtest is lying to you. This library catches it.*

`survival-alpha` is the **methodology layer** that sits underneath any trading strategy. It is not a backtest framework competing with `vectorbt` or `backtrader`. It is a thinner, opinionated layer that enforces backtest hygiene — the controls that turn "a number on a chart" into "a number you'd actually risk capital on."

The brand handoff is direct: *Survival Is Alpha* (the thesis) → `survival-alpha` (the executable form).

## Modules

| Module | Purpose | Substack lineage |
|---|---|---|
| `hygiene/` | Repaint detector, look-ahead-bias checker, data-source audit. The killer module — the reason people install. | "How I Killed The Arsenal Repaint Bug"; "yfinance was lying to us" |
| `backtest/` | Minimal, opinionated runner. Signal-today / trade-tomorrow baked in. No vectorized magic that hides bugs. | The execution model used across every MRE / Arsenal post |
| `sweep/` | Parameter sweeps with Pareto-frontier extraction. Non-dominated set across return / drawdown / turnover. | V5 → V6 workflow; "225 combinations tested"; the 282M sweep |
| `forward/` | Sub-window forward tests. Robustness score across rolling windows. | "7 forward tests, zero failures"; "I ran 6 forward-tests on the MRE" |
| `regime/` | Voter abstraction → regime classifier with configurable hysteresis (symmetric or asymmetric). | MRE architecture, generalized — no proprietary voters shipped |
| `metrics/` | Standard ratios + the branded **Survival-Alpha Score**. | "Survival Is Alpha" thesis page |

## Design stance

**Strategies are pure functions.** A strategy is `signal(state) -> position`, where `state` contains *only data available at time t*. The hygiene layer enforces this at runtime — if a strategy tries to peek at `data[t+1]`, the test fails. This single design choice eliminates the #1 retail quant bug.

## Dependencies (minimal on purpose)

- Required: `pandas`, `numpy`, `scipy.stats`
- Optional: `matplotlib` or `plotly` for tearsheets
- Excluded: `backtrader`, `vectorbt`, any data-feed library

People should add `survival-alpha` to their existing stack, not adopt a framework.

## Phased release

- **v0.1 (MVP, ~2 weekends):** `hygiene.repaint`, `hygiene.lookahead`, minimal `backtest.run`. One demo notebook reproducing a known repaint scenario.
- **v0.2:** `sweep` + `forward` + Pareto selector. Find robust parameters, not lucky ones.
- **v0.3:** `regime` voter framework. The most novel piece — generalizes MRE's architecture.
- **v0.4:** `metrics.survival_alpha_score` + branded single-page PDF tearsheet. The artifact people screenshot.
- **v1.0:** docs polish, examples, public launch.

## Docs strategy

Each module's docs page links to the Substack post that motivated it. The library's narrative documentation is *literally* the DurdenBTC archive, lightly re-edited. The "why this pattern matters" writing already exists — the library is the executable form of it.

## What stays out (protects the edge)

- Your specific voters, weights, parameters from MRE or Arsenal
- Any signal output
- Any specific data-feed integration

The library teaches *how* to backtest right. It does not ship *your* engines.

## Why it should get traction

1. **Brand pre-loaded.** Your audience already understands the philosophy.
2. **Repaint detector is uniquely shippable.** Single-issue demo posts (e.g. "I ran the repaint detector against [popular Substack strategy] — here's what fell out") write themselves.
3. **Regime/voter abstraction is novel in OSS.** Most regime-detection code is bespoke.

## Open questions to resolve before coding

1. **Survival-Alpha Score formula.** What's the canonical metric? A draft: `geometric_return / max_drawdown × (1 − p_ruin)`. Needs thought.
2. **Data model.** Strict pandas? Or accept numpy arrays + a schema?
3. **Voter API.** Class-based (`class Voter`) or functional (`@voter` decorator on a function)?
4. **License.** MIT (max adoption) vs Apache 2 (patent clause).
5. **Package name on PyPI.** `survival-alpha` is likely available; check.
6. **GitHub org.** Personal account vs a `DurdenBTC` org.

## What this gives you

A real open-source library with a clear thesis, a hireable narrative ("authored the canonical backtest-hygiene library in retail quant"), and a marketing channel that already exists (your Substack). Total time to v0.1: a few weekends. Total time to v1.0: a few months of part-time work.
