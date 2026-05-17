# survival-alpha

> Your backtest is lying to you. This library catches it.

A lightweight Python library + CLI for backtest hygiene. Built for retail quants who care whether their numbers are real.

## What it does (v0.1)

**Mode 1 — TradingView trade log analysis.** Drop a TradingView strategy tester CSV into `./data/`, run `sa`, get:

- **Performance:** CAGR, Sharpe, Sortino, Calmar, Max DD, Time in Market
- **Trade stats:** number of trades, win rate, expectancy, profit factor, avg trade duration
- **Lightweight hygiene checks:** P&L reconciliation, suspicious Sharpe, profit concentration, same-bar fills, era concentration

## Requirements

- Python 3.9 or newer
- pip

## Install

Clone the repo and install in editable mode. **Note the trailing `.`** — it's the path argument to `pip install -e` and easy to miss.

### macOS / Linux

```bash
git clone https://github.com/durdenbtc/survival-alpha.git
cd survival-alpha
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Windows (PowerShell)

```powershell
git clone https://github.com/durdenbtc/survival-alpha.git
cd survival-alpha
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

If PowerShell blocks the activation script with an execution-policy error, run this once in an admin PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Windows (Command Prompt)

```cmd
git clone https://github.com/durdenbtc/survival-alpha.git
cd survival-alpha
py -m venv .venv
.venv\Scripts\activate.bat
pip install -e .
```

(Once published to PyPI you'll be able to skip the clone and just `pip install survival-alpha`.)

## Use it

1. In TradingView, run your strategy in the Strategy Tester.
2. **List of Trades → Export → CSV**.
3. Drop the CSV into `./data/` inside this repo.
4. Run the CLI:

```bash
sa
```

That's it. If `data/` contains exactly one CSV it auto-loads; if there are multiple it asks you to pick.

### If `sa` isn't found

The `sa` command is created by pip during install, but on some systems (especially Windows) the install directory isn't on your `PATH`. Two fixes — pick either:

**Option 1 — use the module-form invocation (always works):**

```bash
python -m survival_alpha
```

**Option 2 — add the Scripts directory to PATH.** When you ran `pip install -e .` you may have seen a warning like *"The scripts sa and survival-alpha are installed in '…' which is not on PATH."* Copy that path, add it to your PATH environment variable, restart your terminal, and `sa` will work.

If you're inside an activated virtual environment (recommended), `sa` will be found automatically while the venv is active.

### Other CLI options

```bash
sa --file path/to/some.csv          # skip auto-detection, load this file
sa --data-dir path/to/folder        # scan a different folder
sa tearsheet                        # explicit subcommand (same as `sa`)
```

## Roadmap

- **v0.1:** Mode 1 — trade log tearsheet + lightweight hygiene ← *you are here*
- **v0.2:** Pine Script → Python converter (LLM-assisted)
- **v0.3:** Mode 2 — signal + price series, full repaint detector
- **v0.4:** Mode 3 — strategy-as-function, parameter sweep, sub-window forward tests
- **v1.0:** Survival-Alpha Score, regime-conditional analysis

## License

MIT
