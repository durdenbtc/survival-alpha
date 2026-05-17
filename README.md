<div align="center">

```
██████╗ ██╗   ██╗██████╗ ██████╗ ███████╗███╗   ██╗██████╗ ████████╗ ██████╗
██╔══██╗██║   ██║██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗╚══██╔══╝██╔════╝
██║  ██║██║   ██║██████╔╝██║  ██║█████╗  ██╔██╗ ██║██████╔╝   ██║   ██║     
██║  ██║██║   ██║██╔══██╗██║  ██║██╔══╝  ██║╚██╗██║██╔══██╗   ██║   ██║     
██████╔╝╚██████╔╝██║  ██║██████╔╝███████╗██║ ╚████║██████╔╝   ██║   ╚██████╗
╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═════╝    ╚═╝    ╚═════╝
```

# `survival-alpha`

### *Your backtest is lying to you. This library catches it.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-43%20passing-brightgreen.svg?style=flat-square)](tests/)
[![Version](https://img.shields.io/badge/version-0.1.0-success.svg?style=flat-square)](https://github.com/durdenbtc/survival-alpha)

[![Website](https://img.shields.io/badge/durdenbtc.com-00E5D3?style=for-the-badge&logo=safari&logoColor=white)](https://durdenbtc.com)
[![Substack](https://img.shields.io/badge/Substack-FF6719?style=for-the-badge&logo=substack&logoColor=white)](https://durdenbtc.substack.com/)
[![X](https://img.shields.io/badge/@DurdenBTC-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/DurdenBTC)

</div>

---

A lightweight Python CLI for **backtest hygiene**. Built for retail quants who care whether their numbers are real.

Drop in a TradingView trade log, run one command, get a real tearsheet — with sanity checks that catch the bugs your backtest is quietly hiding.

## What it does (v0.1)

**Mode 1 — TradingView trade log analysis.**

- **Performance:** total return, CAGR, Sharpe, Sortino, Calmar, max drawdown (intra-trade aware), worst trade MAE, annual volatility, time in market
- **Trade stats:** number of trades, win rate, expectancy, profit factor, avg / largest win, avg / largest loss, avg duration
- **Hygiene checks:** trade durations, same-bar fills, P&L reconciliation, suspicious Sharpe, profit concentration, era concentration
- **Annualization:** stocks (252) by default, crypto (365) on flag, or any integer — Sharpe / Sortino / vol scale correctly

---

## Quickstart

You need Python 3.9+ and a tool called **pipx** (think of it as "App Store for Python CLI tools" — it handles all the setup gunk so you don't have to).

### 1. Install pipx (one time, ever)

| OS | Command |
|---|---|
| **macOS** | `brew install pipx && pipx ensurepath` |
| **Windows** | `py -m pip install --user pipx` then `py -m pipx ensurepath` *(then restart your terminal)* |
| **Linux** | `sudo apt install pipx && pipx ensurepath` |

### 2. Install survival-alpha (one command)

```bash
pipx install git+https://github.com/durdenbtc/survival-alpha.git
```

*(Coming soon: `pipx install survival-alpha` from PyPI.)*

### 3. Run it

Easiest — point `sa` at any TradingView trade log on disk:

```bash
sa path/to/your-tradingview-log.csv
```

Or, if you want to batch through several CSVs at once, just run `sa` from any folder:

```bash
sa
```

If there's no `data/` folder it creates one for you. Drop CSVs into `data/`, run `sa` again, and:

- one CSV → it auto-loads
- multiple CSVs → it asks you which one to run

---

## Getting a TradingView trade log

1. Open your strategy on TradingView
2. **Strategy Tester** → **List of Trades** tab
3. Click the **download icon** (top right) → **Export to CSV**
4. Hand the CSV to `sa` using either path above

---

## Sample output

```
📊 Tearsheet
File    your-btc-strategy.csv
Period  2014-05-20 → 2026-05-17  (12.0 years)
Trades  60

📈 Performance                          🎯 Trade stats
  Total return     46,394.3%              Number of trades       60
  CAGR                66.89%              Win rate            68.3%
  Sharpe               7.59*              Expectancy / trade $77.36K
  Sortino             17.41*              Profit factor        4.73
  Calmar               1.36               Avg win           $143.53K
  Max drawdown      -49.01%               Avg loss          $-65.42K
  Worst trade MAE   -25.02%               Largest win         $1.47M
  Annual volatility   6.78%*              Largest loss     $-305.17K
  Time in market     47.5%                Avg duration    34.6 days

🔍 Hygiene checks
  ✅  Trade durations      All trades have non-negative duration.
  ✅  Same-bar fills       No trades enter and exit on the same bar.
  ✅  P&L reconciliation   Per-trade sums match cumulative.
  ❌  Sharpe sanity        Sharpe of 7.59 is extremely high. Likely look-ahead or overfit.
  ❌  Profit concentration Top 3 trades account for 77.9% of profit.
  ✅  Era concentration    Profitable in 11/13 calendar years (85%).

* derived from a pro-rata daily equity curve; Mode 2 gives higher fidelity
```

---

## Other commands

```bash
sa                              # auto-detect a CSV in ./data/
sa my-log.csv                   # load a specific file
sa --data-dir path/to/folder    # scan a different folder
sa --annualization crypto       # annualize Sharpe/Sortino/vol with 365 days
sa --help                       # show all options
```

---

## Crypto vs stocks: annualization

Sharpe, Sortino, and Annual volatility all depend on a "trading days per year" assumption. The wrong one understates or overstates these numbers by a real margin.

| Market | Days/year | Why |
|---|---|---|
| Stocks / ETFs / FX / futures | **252** | ~5 trading days × 50 weeks, minus holidays |
| Crypto (BTC, ETH, etc.) | **365** | Trades 24/7/365 with no closure |

The CLI defaults to `stocks` (252). Pass `--annualization crypto` for any BTC/ETH strategy so Sharpe is comparable to other crypto-quant tooling.

```bash
sa my-btc-log.csv --annualization crypto    # 365 d/y
sa my-spy-log.csv                            # default 252 d/y
sa my-fx-log.csv  --annualization 252        # explicit
sa my-custom.csv  --annualization 168        # any integer also works
```

**Aliases:** `stocks`, `stock`, `equities`, `equity`, `fx`, `forex`, `futures` → 252; `crypto`, `btc` → 365.

The same Sharpe number on the same trade log reads differently under each basis:

| Basis | Sharpe | Annual vol |
|---|---|---|
| stocks (252) | 6.31 | 5.63% |
| crypto (365) | 7.59 | 6.78% |

Ratio between them is always `sqrt(365/252) ≈ 1.204`.

---

## Roadmap

| Version | Feature |
|---|---|
| **v0.1** | Mode 1 — trade log tearsheet + lightweight hygiene ← *you are here* |
| **v0.2** | Pine Script → Python converter (LLM-assisted) |
| **v0.3** | Mode 2 — signal + price series, full repaint detector |
| **v0.4** | Mode 3 — strategy-as-function, parameter sweep, sub-window forward tests |
| **v1.0** | Survival-Alpha Score, regime-conditional analysis |

See [`docs/TODO.md`](docs/TODO.md) for the granular list of follow-ups, feature requests, and known limitations.

---

## Contributing / Developing

Clone, install dev deps, run the tests:

```bash
git clone https://github.com/durdenbtc/survival-alpha.git
cd survival-alpha
python3 -m venv .venv
source .venv/bin/activate           # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

You should see:

```
============================== 43 passed in 0.46s ==============================
```

The test suite covers the loader, all the metrics math (CAGR, Max DD with intra-trade troughs, Sharpe scaling under different annualization bases, profit-factor edge cases, initial-capital derivation), and the hygiene checks.

If PowerShell blocks activation with an execution-policy error, run this once in admin PowerShell: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

PRs welcome. Pick anything from [`docs/TODO.md`](docs/TODO.md) or open an issue with a TradingView CSV that produces weird numbers.

---

## License

[MIT](LICENSE)

---

<div align="center">

**Built by [DurdenBTC](https://durdenbtc.com)**
*Survival Is Alpha*

</div>
