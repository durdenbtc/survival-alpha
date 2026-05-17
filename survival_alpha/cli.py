"""Command-line interface for survival-alpha."""

from pathlib import Path

import click

from survival_alpha.hygiene import run_lightweight_checks
from survival_alpha.loaders import load_tradingview_csv
from survival_alpha.metrics import compute_metrics
from survival_alpha.report import print_tearsheet


DEFAULT_DATA_DIR = Path("data")


@click.group(invoke_without_command=True)
@click.option(
    "--file",
    "-f",
    "file_path",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="CSV file to analyze (skips auto-detection).",
)
@click.option(
    "--data-dir",
    default=str(DEFAULT_DATA_DIR),
    help="Folder to scan for trade logs.",
)
@click.pass_context
def cli(ctx, file_path, data_dir):
    """survival-alpha — backtest hygiene for retail quants.

    Run with no arguments to auto-detect a CSV in ./data/ and print a tearsheet.
    """
    if ctx.invoked_subcommand is not None:
        return
    _run_tearsheet(file_path, data_dir)


@cli.command()
@click.option(
    "--file",
    "-f",
    "file_path",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="CSV file to analyze.",
)
@click.option(
    "--data-dir",
    default=str(DEFAULT_DATA_DIR),
    help="Folder to scan for trade logs.",
)
def tearsheet(file_path, data_dir):
    """Run the Mode 1 tearsheet on a TradingView trade log."""
    _run_tearsheet(file_path, data_dir)


def _run_tearsheet(file_path, data_dir):
    chosen = _pick_file(file_path, data_dir)
    if chosen is None:
        return
    click.echo(f"\nLoading {chosen}\n")
    trades = load_tradingview_csv(chosen)
    metrics = compute_metrics(trades)
    checks = run_lightweight_checks(trades, metrics)
    print_tearsheet(Path(chosen).name, trades, metrics, checks)


def _pick_file(file_path, data_dir):
    if file_path:
        return file_path
    folder = Path(data_dir)
    if not folder.exists():
        click.echo(f"No folder at {folder}/. Create it and drop a TradingView CSV in.")
        return None
    csvs = sorted(folder.glob("*.csv"))
    if not csvs:
        click.echo(f"No CSV files in {folder}/. Drop a TradingView trade log in there.")
        return None
    if len(csvs) == 1:
        click.echo(f"Auto-loading the only file in {folder}/: {csvs[0].name}")
        return str(csvs[0])
    click.echo(f"\nMultiple files in {folder}/:")
    for i, f in enumerate(csvs):
        click.echo(f"  [{i}] {f.name}")
    idx = click.prompt("\nPick one (number)", type=int)
    if 0 <= idx < len(csvs):
        return str(csvs[idx])
    click.echo("Invalid selection.")
    return None
