"""Rich-formatted CLI tearsheet output."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


STATUS_GLYPHS = {
    "pass": ("✅", "green"),
    "warn": ("⚠️ ", "yellow"),
    "fail": ("❌", "red"),
}


def _fmt_pct(x, places=2):
    return f"{x*100:.{places}f}%"


def _fmt_usd(x):
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:,.2f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:,.2f}K"
    return f"${x:,.0f}"


def print_tearsheet(filename, trades, metrics, hygiene_checks):
    console = Console()

    # Header
    header = Text()
    header.append("📊 survival-alpha tearsheet\n", style="bold cyan")
    header.append("File:    ", style="dim")
    header.append(f"{filename}\n", style="bold")
    header.append("Period:  ", style="dim")
    header.append(
        f"{metrics['start_date'].date()} → {metrics['end_date'].date()} "
        f"({metrics['years']:.1f} years)\n",
        style="bold",
    )
    header.append("Trades:  ", style="dim")
    header.append(f"{metrics['n_trades']}", style="bold")
    console.print(Panel(header, box=box.ROUNDED, border_style="cyan"))

    # Performance
    perf = Table(
        title="📈 Performance",
        box=box.SIMPLE_HEAVY,
        show_header=False,
        title_style="bold green",
        padding=(0, 2),
    )
    perf.add_column("Metric", style="bold")
    perf.add_column("Value", justify="right")
    perf.add_row("Total return", _fmt_pct(metrics["total_return"], 1))
    perf.add_row("CAGR", _fmt_pct(metrics["cagr"]))
    perf.add_row("Sharpe", f"{metrics['sharpe']:.2f}")
    perf.add_row("Sortino", f"{metrics['sortino']:.2f}")
    perf.add_row("Calmar", f"{metrics['calmar']:.2f}")
    perf.add_row("Max drawdown", _fmt_pct(metrics["max_dd"]))
    perf.add_row("Max intra-trade DD", _fmt_pct(metrics["max_intra_trade_dd"]))
    perf.add_row("Time in market", _fmt_pct(metrics["time_in_market"], 1))
    console.print(perf)

    # Trade stats
    ts = Table(
        title="🎯 Trade stats",
        box=box.SIMPLE_HEAVY,
        show_header=False,
        title_style="bold blue",
        padding=(0, 2),
    )
    ts.add_column("Metric", style="bold")
    ts.add_column("Value", justify="right")
    ts.add_row("Number of trades", str(metrics["n_trades"]))
    ts.add_row("Win rate", _fmt_pct(metrics["win_rate"], 1))
    ts.add_row("Expectancy / trade", _fmt_usd(metrics["expectancy_usd"]))
    pf = metrics["profit_factor"]
    ts.add_row("Profit factor", "∞" if pf == float("inf") else f"{pf:.2f}")
    ts.add_row("Avg win", _fmt_usd(metrics["avg_win_usd"]))
    ts.add_row("Avg loss", _fmt_usd(metrics["avg_loss_usd"]))
    ts.add_row("Largest win", _fmt_usd(metrics["largest_win_usd"]))
    ts.add_row("Largest loss", _fmt_usd(metrics["largest_loss_usd"]))
    ts.add_row("Avg duration", f"{metrics['avg_duration_days']:.1f} days")
    console.print(ts)

    # Hygiene
    hyg = Table(
        title="🔍 Hygiene checks",
        box=box.SIMPLE_HEAVY,
        title_style="bold magenta",
        padding=(0, 1),
    )
    hyg.add_column("", width=3)
    hyg.add_column("Check", style="bold", no_wrap=True)
    hyg.add_column("Result")
    for c in hygiene_checks:
        glyph, color = STATUS_GLYPHS[c.status]
        hyg.add_row(glyph, c.name, Text(c.message, style=color))
    console.print(hyg)

    # Footer
    footer = Text()
    footer.append("\nNote: ", style="dim bold")
    footer.append(
        "Sharpe/Sortino are computed from a pro-rata daily equity curve. "
        "For higher-fidelity metrics including true repaint detection, "
        "upgrade to Mode 2 (signal + price series). — survival-alpha v0.1\n",
        style="dim italic",
    )
    console.print(footer)
