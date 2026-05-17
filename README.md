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

[![Website](https://img.shields.io/badge/durdenbtc.com-FF9900?style=for-the-badge&logo=safari&logoColor=white)](https://durdenbtc.com)
[![Substack](https://img.shields.io/badge/Substack-FF6719?style=for-the-badge&logo=substack&logoColor=white)](https://durdenbtc.substack.com/)
[![X](https://img.shields.io/badge/@DurdenBTC-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/DurdenBTC)

</div>

---

A lightweight Python CLI for **backtest hygiene**. Built for retail quants who care whether their numbers are real.

Drop your TradingView trade log into a folder, run one command, get a real tearsheet — with sanity checks that catch the bugs your backtest is quietly hiding.

## What it does (v0.1)

**Mode 1 — TradingView trade log analysis.**

- **Performance:** CAGR, Sharpe, Sortino, Calmar, Max DD, Time in Market
- **Trade stats:** number of trades, win rate, expectancy, profit factor, avg trade duration
- **Hygiene checks:** P&L reconciliation, suspicious Sharpe, profit concentration, same-bar fills, era concentration

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

### 3. Use it

```bash
mkdir survival-alpha-data
cd survival-alpha-data
mkdir data
# drop your TradingView CSV into the data/ folder, then:
sa
```

That's it. If `data/` contains exactly one CSV it auto-loads; if there are multiple it asks you which one to run.

---

## Getting a TradingView trade log

1. Open your strategy on TradingView
2. **Strategy Tester** → **List of Trades** tab
3. Click the **download icon** in the top right → **Export to CSV**
4. Drop the file into the `data/` folder next to where you're running `sa`

---

## Other commands

```bash
sa                                  # auto-detect a CSV in ./data/ and run the tearsheet
sa --file path/to/some.csv          # skip auto-detection
sa --data-dir path/to/folder        # scan a different folder
sa tearsheet                        # explicit subcommand (same as `sa` with no args)
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
