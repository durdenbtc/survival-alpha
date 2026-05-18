# convert/ — drop your Pine pipeline files here

When you run `sa convert` from the repo root, this folder gets auto-scanned for:

- **One `.pine` file** — the strategy source
- **An OHLC CSV** — yfinance-format with `Date / Open / High / Low / Close` columns
- *(optional)* **A TradingView trade-log CSV** — to diff the generated trades against

The CLI tells them apart by inspecting CSV headers:
- `Trade #` column → TradingView reference
- `Open/High/Low/Close` columns → OHLC price data

Anything in this folder is gitignored except this README and `.gitkeep`,
so your strategy files stay local.

Run from the repo root:

```bash
sa convert
```
