# survival-alpha

> Your backtest is lying to you. This library catches it.

A lightweight Python library + CLI for backtest hygiene. Built for retail quants who care whether their numbers are real.

## What it does (v0.1)

**Mode 1 — TradingView trade log analysis.** Drop a TradingView strategy tester CSV into `./data/`, run `sa`, get:

- **Performance:** CAGR, Sharpe, Sortino, Calmar, Max DD, Time in Market
- **Trade stats:** number of trades, win rate, expectancy, profit factor, avg trade duration
- **Lightweight hygiene checks:** P&L reconciliation, suspicious Sharpe, profit concentration, same-bar fills, era concentration

## Install

```bash
pip install -e .
```

(Coming soon: `pip install survival-alpha` from PyPI.)

## Use it

Export your TradingView strategy tester results to CSV. Drop the CSV into `./data/`. Then:

```bash
sa
```

That's it. If there's only one CSV in `data/` it auto-loads. Multiple, and it asks.

## Roadmap

- **v0.1:** Mode 1 — trade log tearsheet + lightweight hygiene ← *you are here*
- **v0.2:** Pine Script → Python converter (LLM-assisted)
- **v0.3:** Mode 2 — signal + price series, full repaint detector
- **v0.4:** Mode 3 — strategy-as-function, parameter sweep, sub-window forward tests
- **v1.0:** Survival-Alpha Score, regime-conditional analysis

## License

MIT
