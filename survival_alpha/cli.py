"""Command-line interface for survival-alpha."""

from pathlib import Path

import click

import re

import pandas as pd
from rich.console import Console

from survival_alpha.hygiene import run_lightweight_checks
from survival_alpha.loaders import load_tradingview_csv
from survival_alpha.metrics import compute_metrics
from survival_alpha.report import print_brand_header, print_tearsheet
from survival_alpha.converter import (
    ParseError,
    diff_trades,
    parse_sma_crossover,
    run_strategy,
    translate,
)
from survival_alpha.converter.cli_view import (
    render_backtest_panel,
    render_diff_panel,
    render_parse_panel,
    render_translation_panel,
)


DEFAULT_DATA_DIR = "data"


@click.group(invoke_without_command=True)
@click.option(
    "--file", "-f", "file_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default=None,
    help="TradingView trade log CSV (skips auto-detection).",
)
@click.option(
    "--data-dir",
    default=DEFAULT_DATA_DIR,
    help=f"Folder to scan for trade logs when no file is given (default: ./{DEFAULT_DATA_DIR}/).",
)
@click.option(
    "--annualization",
    default="stocks",
    show_default=True,
    help="Trading days per year for Sharpe/Sortino/vol. "
         "Use 'stocks' (252), 'crypto' (365), or an integer.",
)
@click.pass_context
def cli(ctx, file_path, data_dir, annualization):
    """survival-alpha — backtest hygiene for retail quants.

    \b
    Mode 1 — tearsheet on a TradingView trade log:
      sa                              (auto-detect a CSV in ./data/)
      sa --file my-log.csv            (explicit file)
      sa tearsheet my-log.csv         (same, explicit subcommand)

    \b
    Mode 2 — Pine -> Python conversion (v0.2):
      sa convert foo.pine                       (translate only)
      sa convert foo.pine -d btc.csv            (+ backtest)
      sa convert foo.pine -d btc.csv -r tv.csv  (+ diff vs TradingView)
    """
    if ctx.invoked_subcommand is not None:
        return
    _run_tearsheet(file_path, data_dir, annualization)


@cli.command()
@click.argument(
    "file_path",
    required=False,
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
@click.option("--data-dir", default=DEFAULT_DATA_DIR)
@click.option("--annualization", default="stocks", show_default=True,
              help="'stocks' (252), 'crypto' (365), or an integer.")
def tearsheet(file_path, data_dir, annualization):
    """Run the Mode 1 tearsheet on a TradingView trade log."""
    _run_tearsheet(file_path, data_dir, annualization)


@cli.command()
@click.argument(
    "pine_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
@click.option(
    "--data", "-d", "data_path",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="OHLC CSV (yfinance format) to backtest the translated strategy on.",
)
@click.option(
    "--reference", "-r", "reference_path",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="TradingView trade-log CSV to diff the generated trades against.",
)
@click.option(
    "--output", "-o", "output_dir",
    default="generated",
    show_default=True,
    help="Directory to write the generated Python file.",
)
@click.option("--initial-capital", type=float, default=10_000.0, show_default=True)
@click.option("--order-size-pct", type=float, default=99.0, show_default=True,
              help="Position size as percent of current equity.")
@click.option("--commission-pct", type=float, default=0.0, show_default=True,
              help="Commission per side as a percent of trade size.")
def convert(pine_path, data_path, reference_path, output_dir,
            initial_capital, order_size_pct, commission_pct):
    """Translate a Pine Script SMA crossover strategy to Python.

    \b
    Three modes:
      sa convert foo.pine                       (translate only)
      sa convert foo.pine -d btc.csv            (translate + backtest)
      sa convert foo.pine -d btc.csv -r tv.csv  (translate + backtest + diff)
    """
    console = Console()
    print_brand_header(console)
    _run_convert(
        console, Path(pine_path), data_path, reference_path, output_dir,
        initial_capital, order_size_pct, commission_pct,
    )


def _run_convert(console, pine_path, data_path, reference_path, output_dir,
                 initial_capital, order_size_pct, commission_pct):
    # 1. Parse
    try:
        spec = parse_sma_crossover(pine_path.read_text(encoding="utf-8"))
    except ParseError as e:
        raise click.ClickException(f"Pine parse error: {e}")
    render_parse_panel(console, spec, pine_path)

    # 2. Translate + write
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", spec.strategy_name).strip("_").lower()
    if not safe:
        safe = "strategy"
    out_file = out_dir / f"{safe}.py"
    code = translate(spec)
    out_file.write_text(code, encoding="utf-8")
    render_translation_panel(console, out_file, len(code.splitlines()))

    # 3. Backtest if --data provided
    if data_path is None:
        console.print(
            "\nPass [bold]--data path/to/ohlc.csv[/bold] to backtest the generated strategy."
        )
        return

    data = _load_ohlc(Path(data_path))
    ns = {}
    exec(code, ns)
    trades = run_strategy(
        ns["strategy"], data,
        tv_config={
            "initial_capital": initial_capital,
            "order_size_pct": order_size_pct,
            "commission_pct": commission_pct,
        },
    )
    render_backtest_panel(
        console, Path(data_path).name, trades, len(data),
        data.index.min(), data.index.max(),
    )

    # 4. Diff against reference if provided
    if reference_path is None:
        console.print(
            "\nPass [bold]--reference path/to/tv_trades.csv[/bold] to diff against TradingView's output."
        )
        return

    ref = load_tradingview_csv(reference_path)
    diff = diff_trades(trades, ref)
    render_diff_panel(console, diff)


def _load_ohlc(path):
    """Load an OHLC CSV (yfinance format: Date, Open, High, Low, Close[, Volume])."""
    df = pd.read_csv(path)
    date_col = next(
        (c for c in df.columns if c.lower() in ("date", "datetime", "timestamp")),
        None,
    )
    if date_col is None:
        raise click.BadParameter(
            f"OHLC CSV must have a Date/Datetime/Timestamp column. Got: {list(df.columns)}"
        )
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()
    df.index.name = "Date"
    required = {"Open", "High", "Low", "Close"}
    missing = required - set(df.columns)
    if missing:
        raise click.BadParameter(f"OHLC CSV is missing columns: {sorted(missing)}")
    return df


def _run_tearsheet(file_path, data_dir, annualization="stocks"):
    chosen = _pick_file(file_path, data_dir)
    if chosen is None:
        return
    click.echo(f"\nLoading {chosen}\n")
    trades = load_tradingview_csv(chosen)
    try:
        metrics = compute_metrics(trades, annualization=annualization)
    except ValueError as e:
        raise click.BadParameter(str(e))
    checks = run_lightweight_checks(trades, metrics)
    print_tearsheet(Path(chosen).name, trades, metrics, checks)


def _pick_file(file_path, data_dir):
    """Resolve which CSV to analyze.

    Priority: explicit file path > auto-detect single CSV in ./data/ >
    interactive pick if multiple. If ./data/ doesn't exist we create it
    and tell the user what to do next.
    """
    if file_path:
        return file_path
    folder = Path(data_dir)
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        click.echo(
            f"\nCreated ./{folder}/ for you. Drop a TradingView CSV in there "
            f"and re-run `sa`.\n\nOr point directly at a file:\n"
            f"  sa path/to/your-log.csv\n"
        )
        return None
    csvs = sorted(folder.glob("*.csv"))
    if not csvs:
        click.echo(
            f"\nNo CSV files in ./{folder}/. Drop a TradingView trade log "
            f"in there, or point directly at a file:\n"
            f"  sa path/to/your-log.csv\n"
        )
        return None
    if len(csvs) == 1:
        click.echo(f"Auto-loading the only file in ./{folder}/: {csvs[0].name}")
        return str(csvs[0])
    click.echo(f"\nMultiple files in ./{folder}/:")
    for i, f in enumerate(csvs):
        click.echo(f"  [{i}] {f.name}")
    idx = click.prompt("\nPick one (number)", type=int)
    if 0 <= idx < len(csvs):
        return str(csvs[idx])
    click.echo("Invalid selection.")
    return None
