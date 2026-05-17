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

- **Performance:** total return, CAGR, Sharpe, Sortino, Calmar, max drawdown, max intra-trade DD, annual volatility, time in market
- **Trade stats:** number of trades, win rate, expectancy, profit factor, avg / largest win, avg / largest loss, avg duration
- **Hygiene checks:** trade durations, same-bar fills, P&L reconciliation, suspicious Sharpe, profit concentration, era concentration

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

## Other commands

```bash
sa                              # auto-detect a CSV in ./data/
sa my-log.csv                   # load a specific file
sa --data-dir path/to/folder    # scan a different folder
sa --help                       # show all options
```

---

## Roadmap

| Version | Feature |
|---|---|
| **v0.1** | Mode 1 — trade log tearsheet + lightweight hygiene ← *you are here* |
| **v0.2** | Pine Script → Python converter (LLM-assisted) |
| **v0.3** | Mode 2 — signal + price series, full repaint detector |
| **v0.4** | Mode 3 — strategy-as-function, parameter sweep, sub-window forward tests |
| **v1.0** | Survival-Alpha Score, regime-conditional analysis |

---

## Developing

If you want to hack on the code rather than just use it:

```bash
git clone https://github.com/durdenbtc/survival-alpha.git
cd survival-alpha
python3 -m venv .venv
source .venv/bin/activate           # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
sa
```

If PowerShell blocks activation with an execution-policy error, run this once in admin PowerShell: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

---

## License

[MIT](LICENSE)

---

<div align="center">

**Built by [DurdenBTC](https://durdenbtc.com)**
*Survival Is Alpha*

</div>
